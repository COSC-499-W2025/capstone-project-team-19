"""
Code Complexity and Structure Analyzer

This module analyzes code complexity and structure metrics using:
- Radon: Cyclomatic complexity, Maintainability Index, raw metrics
- Lizard: Code metrics including LOC, CCN, token count, parameters

Provides comprehensive code quality metrics for individual coding projects.
"""

import os
from typing import Dict, List, Optional
from radon.complexity import cc_visit, cc_rank
from radon.metrics import mi_visit, mi_rank
from radon.raw import analyze as raw_analyze
import lizard
from src.extension_catalog import get_languages_for_extension


def analyze_code_complexity(conn, user_id: int, project_name: str, zip_path: str) -> Dict:
    """
    Analyze code complexity for all code files in a project.

    Returns a dictionary containing:
    - radon_metrics: Cyclomatic complexity, Maintainability Index
    - lizard_metrics: LOC, CCN, token count, parameters
    - project_summary: Aggregated metrics
    """

    # Get all code files from the database
    cursor = conn.cursor()
    query = """
        SELECT file_name, file_path
        FROM files
        WHERE user_id = ? AND project_name = ? AND file_type = 'code'
    """
    cursor.execute(query, (user_id, project_name))
    files = cursor.fetchall()

    if not files:
        print(f"No code files found for project '{project_name}'")
        return {}

    # Determine base path for the extracted files
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_data_dir = os.path.join(repo_root, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(zip_data_dir, zip_name)

    radon_results = []
    lizard_results = []

    print(f"\n{'='*80}")
    print(f"Analyzing Code Complexity and Structure for: {project_name}")
    print(f"{'='*80}\n")

    # Files to skip (Git internals, binaries, etc.)
    skip_extensions = {'.pack', '.idx', '.sample', '.git', '.lock'}
    skip_patterns = {'pack-', 'idx-'}

    for file_name, file_path in files:
        full_path = os.path.join(base_path, file_path)

        if not os.path.exists(full_path):
            continue

        # Get file extension and detect languages
        file_ext = os.path.splitext(file_name)[1].lower()

        # Skip Git internal files and other non-code files
        if file_ext in skip_extensions:
            print(f"Skipping Git internal file: {file_name}")
            continue

        # Skip files with certain name patterns
        if any(pattern in file_name.lower() for pattern in skip_patterns):
            print(f"Skipping Git internal file: {file_name}")
            continue

        # Skip very large files (> 5MB) to avoid hangs
        try:
            file_size = os.path.getsize(full_path)
            if file_size > 5 * 1024 * 1024:  # 5MB
                print(f"Skipping large file ({file_size / (1024*1024):.1f}MB): {file_name}")
                continue
        except OSError:
            continue

        # Detect languages for this file using extension catalog
        languages = get_languages_for_extension(file_ext)

        # Skip files with no recognized languages
        if not languages:
            continue

        print(f"Analyzing: {file_name}...")

        # Analyze with Radon (Python only)
        is_python = 'Python' in languages
        radon_data = analyze_with_radon(full_path, file_name, is_python)
        if radon_data:
            radon_results.append(radon_data)

        # Analyze with Lizard (multi-language)
        lizard_data = analyze_with_lizard(full_path, file_name)
        if lizard_data:
            lizard_results.append(lizard_data)

    # Aggregate results
    summary = aggregate_complexity_metrics(radon_results, lizard_results)

    return {
        'radon_metrics': radon_results,
        'lizard_metrics': lizard_results,
        'summary': summary
    }


def analyze_with_radon(file_path: str, file_name: str, is_python: bool) -> Optional[Dict]:
    """
    Analyze a single file using Radon for:
    - Cyclomatic Complexity (CC)
    - Maintainability Index (MI)
    - Raw metrics (LOC, SLOC, comments, etc.)

    Note: Radon is primarily for Python. Skip non-Python files.
    """
    try:
        # Radon works only with Python files
        if not is_python:
            # Skip non-Python files for Radon analysis
            return None

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        # Cyclomatic Complexity
        cc_results = cc_visit(code)
        complexity_scores = []
        for item in cc_results:
            complexity_scores.append({
                'name': item.name,
                'complexity': item.complexity,
                'rank': cc_rank(item.complexity),
                'lineno': item.lineno
            })

        # Maintainability Index
        mi_score = mi_visit(code, multi=True)
        mi_value = mi_score if isinstance(mi_score, (int, float)) else 0
        mi_rating = mi_rank(mi_value)

        # Raw metrics
        raw_metrics = raw_analyze(code)

        return {
            'file_name': file_name,
            'cyclomatic_complexity': complexity_scores,
            'average_complexity': sum(item.complexity for item in cc_results) / len(cc_results) if cc_results else 0,
            'maintainability_index': mi_value,
            'maintainability_rank': mi_rating,
            'loc': raw_metrics.loc,
            'lloc': raw_metrics.lloc,  # Logical LOC
            'sloc': raw_metrics.sloc,  # Source LOC
            'comments': raw_metrics.comments,
            'multi': raw_metrics.multi,  # Multi-line strings
            'blank': raw_metrics.blank
        }

    except Exception as e:
        print(f"Error analyzing {file_name} with Radon: {e}")
        return None


def analyze_with_lizard(file_path: str, file_name: str) -> Optional[Dict]:
    """
    Analyze a single file using Lizard for:
    - Lines of Code (LOC)
    - Cyclomatic Complexity Number (CCN)
    - Token count
    - Parameter count
    - Function length
    """
    try:
        analysis = lizard.analyze_file(file_path)

        functions = []
        for func in analysis.function_list:
            # Lizard's parameters might be a list or count depending on version
            param_count = len(func.parameters) if isinstance(func.parameters, list) else func.parameters

            functions.append({
                'name': func.name,
                'lines': func.nloc,
                'ccn': func.cyclomatic_complexity,
                'token_count': func.token_count,
                'parameters': param_count,
                'start_line': func.start_line,
                'end_line': func.end_line
            })

        return {
            'file_name': file_name,
            'nloc': analysis.nloc,  # Lines of code without comments
            'average_nloc': analysis.average_nloc,
            'average_ccn': analysis.average_cyclomatic_complexity,
            'average_token': analysis.average_token_count,
            'functions': functions,
            'function_count': len(functions)
        }

    except Exception as e:
        print(f"Error analyzing {file_name} with Lizard: {e}")
        return None


def aggregate_complexity_metrics(radon_results: List[Dict], lizard_results: List[Dict]) -> Dict:
    """
    Aggregate complexity metrics across all files in the project.
    Returns actionable summary with key metrics and recommendations.
    """
    if not radon_results and not lizard_results:
        return {}

    # Initialize comprehensive summary
    # Use max of both since Radon might skip non-Python files
    total_files_analyzed = max(len(radon_results), len(lizard_results))

    summary = {
        'total_files': total_files_analyzed,
        'successful': total_files_analyzed,
        'total_lines': 0,
        'total_code': 0,
        'total_comments': 0,
        'total_functions': 0,
        'avg_complexity': 0,
        'avg_maintainability': 0,
        'functions_needing_refactor': 0,
        'high_complexity_files': 0,
        'low_maintainability_files': 0,
        'complexity_distribution': {},
        'most_complex_functions': [],
        'radon_details': {},
        'lizard_details': {}
    }

    # Aggregate Radon metrics
    if radon_results:
        total_loc = sum(r.get('loc', 0) for r in radon_results)
        total_sloc = sum(r.get('sloc', 0) for r in radon_results)
        total_comments = sum(r.get('comments', 0) for r in radon_results)
        avg_complexity = sum(r.get('average_complexity', 0) for r in radon_results) / len(radon_results)
        avg_mi = sum(r.get('maintainability_index', 0) for r in radon_results) / len(radon_results)

        # Count complexity ranks
        rank_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
        total_high_complexity_funcs = 0

        for result in radon_results:
            for func in result.get('cyclomatic_complexity', []):
                rank = func.get('rank', 'A')
                if rank in rank_counts:
                    rank_counts[rank] += 1
                # Functions with rank D, E, F need refactoring
                if rank in ['D', 'E', 'F']:
                    total_high_complexity_funcs += 1

        # Count files with low maintainability (< 65)
        low_mi_files = sum(1 for r in radon_results if r.get('maintainability_index', 100) < 65)

        # Count files with high average complexity (> 10)
        high_complexity_files = sum(1 for r in radon_results if r.get('average_complexity', 0) > 10)

        summary.update({
            'total_lines': total_loc,
            'total_code': total_sloc,
            'total_comments': total_comments,
            'avg_complexity': round(avg_complexity, 2),
            'avg_maintainability': round(avg_mi, 2),
            'functions_needing_refactor': total_high_complexity_funcs,
            'low_maintainability_files': low_mi_files,
            'high_complexity_files': high_complexity_files,
            'complexity_distribution': rank_counts
        })

        summary['radon_details'] = {
            'comment_ratio': round((total_comments / total_loc * 100) if total_loc > 0 else 0, 2),
            'maintainability_rank': mi_rank(avg_mi),
            'blank_lines': sum(r.get('blank', 0) for r in radon_results),
            'multi_line_strings': sum(r.get('multi', 0) for r in radon_results)
        }

    # Aggregate Lizard metrics
    if lizard_results:
        total_nloc = sum(r.get('nloc', 0) for r in lizard_results)
        total_functions = sum(r.get('function_count', 0) for r in lizard_results)
        avg_ccn = sum(r.get('average_ccn', 0) for r in lizard_results) / len(lizard_results) if lizard_results else 0
        avg_token = sum(r.get('average_token', 0) for r in lizard_results) / len(lizard_results) if lizard_results else 0

        # Find most complex functions
        all_functions = []
        for result in lizard_results:
            for func in result.get('functions', []):
                all_functions.append({
                    'file': result['file_name'],
                    'name': func['name'],
                    'ccn': func['ccn'],
                    'lines': func['lines'],
                    'token_count': func['token_count'],
                    'parameters': func['parameters']
                })

        # Sort by complexity
        most_complex = sorted(all_functions, key=lambda x: x['ccn'], reverse=True)[:10]

        # Functions with CCN > 15 need refactoring
        high_ccn_funcs = sum(1 for f in all_functions if f['ccn'] > 15)

        summary.update({
            'total_functions': total_functions,
            'most_complex_functions': most_complex[:5]  # Top 5 for display
        })

        # If Radon didn't provide line counts (non-Python project), use Lizard's
        if summary['total_lines'] == 0:
            summary['total_lines'] = total_nloc
            summary['total_code'] = total_nloc

        # Add to functions needing refactor
        summary['functions_needing_refactor'] = max(
            summary['functions_needing_refactor'],
            high_ccn_funcs
        )

        summary['lizard_details'] = {
            'total_nloc': total_nloc,
            'average_ccn': round(avg_ccn, 2),
            'average_token_count': round(avg_token, 2),
            'average_parameters': round(sum(f['parameters'] for f in all_functions) / len(all_functions), 2) if all_functions else 0,
            'functions_with_high_ccn': high_ccn_funcs,
            'longest_function': max(all_functions, key=lambda x: x['lines'])['lines'] if all_functions else 0
        }

    return summary


def display_complexity_results(complexity_data: Dict) -> None:
    """
    Display complexity analysis results in a readable, actionable format.
    """
    if not complexity_data:
        print("No complexity data to display.")
        return

    summary = complexity_data.get('summary', {})

    print(f"\n{'='*80}")
    print("CODE COMPLEXITY & STRUCTURE ANALYSIS")
    print(f"{'='*80}\n")

    # Overview statistics
    print("OVERVIEW:")
    print(f"  Total Files Analyzed: {summary.get('total_files', 0)}")
    print(f"  Successful: {summary.get('successful', 0)}")
    print(f"  Total Lines: {summary.get('total_lines', 0)}")
    print(f"  Total Code Lines: {summary.get('total_code', 0)}")
    print(f"  Total Comments: {summary.get('total_comments', 0)}")
    print(f"  Total Functions: {summary.get('total_functions', 0)}")
    print()

    # Quality metrics
    radon_details = summary.get('radon_details', {})
    if radon_details:
        print("QUALITY METRICS (Python-specific):")
        print(f"  Average Complexity: {summary.get('avg_complexity', 0)}")
        print(f"  Average Maintainability: {summary.get('avg_maintainability', 0):.2f}")
        print(f"  Maintainability Rank: {radon_details.get('maintainability_rank', 'N/A')}")
        print(f"  Comment Ratio: {radon_details.get('comment_ratio', 0):.1f}%")
        print()
    elif summary.get('total_functions', 0) > 0:
        # Show Lizard metrics if no Radon data
        lizard_details = summary.get('lizard_details', {})
        print("QUALITY METRICS:")
        print(f"  Average Complexity (CCN): {lizard_details.get('average_ccn', 0)}")
        print()
    lizard_details = summary.get('lizard_details', {})
    if lizard_details:
        print("ADDITIONAL METRICS:")
        print(f"  Average CCN: {lizard_details.get('average_ccn', 0)}")
        print(f"  Average Token Count: {lizard_details.get('average_token_count', 0)}")
        print(f"  Average Parameters: {lizard_details.get('average_parameters', 0)}")
        print(f"  Longest Function: {lizard_details.get('longest_function', 0)} lines")
        print()

    print(f"{'='*80}\n")

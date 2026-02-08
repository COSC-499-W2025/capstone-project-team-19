import os
import textwrap
import re
from typing import Any, Dict, Optional
from src.utils.helpers import extract_code_file, extract_readme_file, read_file_content
from dotenv import load_dotenv
from groq import Groq
from src.utils.language_detector import detect_languages
from src.utils.framework_detector import detect_frameworks
from .code_llm_analyze_helper import _infer_project_root_folder, _readme_mentions_detected_tech

try:
    from src import constants
except ModuleNotFoundError:
    import constants

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def run_code_llm_analysis(
    parsed_files,
    zip_path,
    project_name=None,
    focus_file_paths=None,
    conn=None,
    user_id=None,
    detected_languages=None,     
    detected_frameworks=None,    
) -> Optional[Dict[str, Any]]:

    if not isinstance(parsed_files, list):
        return None

    # 1. Select code files
    all_code_files = [f for f in parsed_files if f.get("file_type") == "code"]
    if not all_code_files:
        print("No code files found to analyze.")
        return None

    code_files = all_code_files

    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)

    # Infer the likely project root folder EARLY (and do NOT let focus_file_paths shrink it)
    project_root_folder = _infer_project_root_folder(all_code_files, project_name, zip_name=zip_name)

    # Project files = everything in that project folder (used for PROJECT summary)
    project_code_files = code_files
    if project_root_folder:
        prefixes = [
            f"{zip_name}/{project_root_folder}/",
            f"{zip_name}/individual/{project_root_folder}/",
            f"{zip_name}/collaborative/{project_root_folder}/",
            f"{zip_name}/collab/{project_root_folder}/",
            f"{project_root_folder}/",  # fallback if zip_name isn't in paths
        ]

        project_code_files = [
            f for f in all_code_files
            if any((f.get("file_path") or "").replace("\\", "/").startswith(p) for p in prefixes)
        ]

    # Contribution files = optionally focus-filtered (used for CONTRIBUTION summary)
    contrib_code_files = project_code_files

    # If we know which files the user actually touched, restrict to those
    if focus_file_paths:
        normalized_focus = [p.replace("\\", "/") for p in focus_file_paths]
        filtered = []

        for f in project_code_files:
            fp = (f.get("file_path") or "").replace("\\", "/")
            # Match if the parsed path *ends with* one of the focus paths
            if any(fp.endswith(target) for target in normalized_focus):
                filtered.append(f)

        if filtered:
            contrib_code_files = filtered

    if constants.VERBOSE:
        print(f"\n{'='*80}")
        print(f"Analyzing {len(contrib_code_files)} file(s) using LLM-based analysis...")
        print(f"{'='*80}\n")
        # DEBUG: helps confirm we are not analyzing the same files for every project
        print(f"DEBUG zip_name: {zip_name}")
        print(f"DEBUG project_name (arg): {project_name}")
        print(f"DEBUG inferred project_root_folder: {project_root_folder}")
        print(f"DEBUG all_code_files: {len(all_code_files)}")
        print(f"DEBUG project_code_files (for project summary): {len(project_code_files)}")
        print(f"DEBUG contrib_code_files (for contribution summary): {len(contrib_code_files)}")
        print("DEBUG sample project_code_files:")
        for x in project_code_files[:5]:
            print("  -", (x.get("file_path") or ""), "|", (x.get("file_name") or ""))
        print("DEBUG sample contrib_code_files:")
        for x in contrib_code_files[:5]:
            print("  -", (x.get("file_path") or ""), "|", (x.get("file_name") or ""))
        print(f"\n{'='*80}\n")

    readme_text = None

    # Determine which relative project directory actually matches the parsed file paths.
    # Supports:
    #   zip_name/project_name/...
    #   zip_name/individual/project_name/...
    #   zip_name/collaborative/project_name/...
    project_dir_rel = None
    if project_root_folder:
        project_dir_rel_candidates = [
            f"{zip_name}/{project_root_folder}",
            f"{zip_name}/individual/{project_root_folder}",
            f"{zip_name}/collaborative/{project_root_folder}",
            f"{zip_name}/collab/{project_root_folder}",
            f"{project_root_folder}",  # fallback if zip_name isn't in paths
        ]

        for cand in project_dir_rel_candidates:
            cand_prefix = cand + "/"
            if any(((f.get("file_path") or "").replace("\\", "/")).startswith(cand_prefix) for f in all_code_files):
                project_dir_rel = cand
                break

        if constants.VERBOSE:
            print("DEBUG project_dir_rel used for README:", project_dir_rel)

        if project_dir_rel:
            readme_text = extract_readme_file(os.path.join(base_path, project_dir_rel))

    # Do NOT fall back to zip root README for per-project summaries
    # (it contaminates summaries with other projects' README content)
    if not readme_text:
        readme_text = None
        if constants.VERBOSE:
            print("DEBUG README: none found in project folder; using CODE_CONTEXT for project summary")

    if readme_text and len(readme_text) > 8000:
        readme_text = readme_text[:8000]

        # 3. Infer a project name if not provided
    project_folders = sorted(
        set(os.path.dirname(f["file_path"]).split(os.sep)[0] for f in project_code_files)
    )
    if not project_name:
        project_name = project_folders[0] if project_folders else zip_name

    # NEW: Tech stack evidence from existing detectors (no duplication)
    detected_languages = []
    detected_frameworks = []

    # ALWAYS define this first (prevents UnboundLocalError)
    tech_stack_block = (
        "TECH STACK (evidence-based):\n"
        "- Languages: Unknown\n"
        "- Frameworks: Unknown\n"
    )

    # If we have DB context, fill it with real values
    if conn is not None and user_id is not None:
        try:
            detected_languages = detect_languages(conn, user_id, project_name)
        except Exception as e:
            if constants.VERBOSE:
                print("DEBUG detect_languages failed:", e)

        try:
            detected_frameworks = sorted(list(detect_frameworks(conn, project_name, user_id, zip_path)))
        except Exception as e:
            if constants.VERBOSE:
                print("DEBUG detect_frameworks failed:", e)

        tech_stack_block = (
            "TECH STACK (evidence-based):\n"
            f"- Languages: {', '.join(detected_languages) if detected_languages else 'Unknown'}\n"
            f"- Frameworks: {', '.join(detected_frameworks) if detected_frameworks else 'Unknown'}\n"
        )

    if constants.VERBOSE:
        print("DEBUG detected_languages:", detected_languages)
        print("DEBUG detected_frameworks:", detected_frameworks)
        print("DEBUG tech_stack_block ready")

    readme_tech_ok = False
    if readme_text:
        readme_tech_ok = (
            len(readme_text) >= 1500 and
            _readme_mentions_detected_tech(readme_text, detected_languages, detected_frameworks)
        )

    if constants.VERBOSE:
        print("DEBUG readme_tech_ok (README mentions detected tech):", readme_tech_ok)

    # We now build TWO contexts:
    #  - project_context_parts: README + code snippets (for project summary)
    #  - contrib_context_parts: code snippets ONLY (for contribution summary)
    project_context_parts: list[str] = []
    contrib_context_parts: list[str] = []

    # If readme present: use readme, code context, tech stack
    # Otherwise: only code context and tech stack
    if readme_text:
        project_context_parts.append(f"README:\n{readme_text}")

    # Always include tech stack evidence
    project_context_parts.append(tech_stack_block)

    # 2. Build context from code files
    # PROJECT context: use ALL project files (ignore focus_file_paths here)
    for file_info in project_code_files:
        file_path = os.path.join(base_path, file_info["file_path"])

        # For focused collaborative analysis, use full file contents.
        # For other cases, keep the lighter "headers + comments" mode.
        code_context = extract_code_file(file_path)

        if code_context:
            snippet = f"### {file_info['file_name']} ###\n{code_context}"
            project_context_parts.append(snippet)

    # CONTRIBUTION context: use focused files if provided (or all project files otherwise)
    for file_info in contrib_code_files:
        file_path = os.path.join(base_path, file_info["file_path"])

        # For focused collaborative analysis, use full file contents.
        # For other cases, keep the lighter "headers + comments" mode.
        if focus_file_paths:
            code_context = read_file_content(file_path)
        else:
            code_context = extract_code_file(file_path)

        if code_context:
            snippet = f"### {file_info['file_name']} ###\n{code_context}"
            contrib_context_parts.append(snippet)

    project_context = "\n\n".join(project_context_parts)
    if len(project_context) > 12000:
        project_context = project_context[:12000]

    contribution_context = "\n\n".join(contrib_context_parts)

    if not project_context:
        print("No readable code context found. Skipping LLM analysis.\n")
        return None

    # If somehow no code made it into contrib_context, fall back to project_context
    # (rare; but keeps behaviour from totally breaking).
    if not contribution_context:
        contribution_context = project_context

    # 4. Call the existing LLM helpers
    #    - Project summary: README + light code context
    #    - Contribution summary: CODE-ONLY context (no README content)
    project_summary = generate_code_llm_project_summary(project_context, readme_tech_ok)
    contribution_summary = generate_code_llm_contribution_summary(contribution_context)

    display_code_llm_results(
        project_name,
        project_summary,
        contribution_summary,
        mode="COLLABORATIVE" if "collab" in (project_name or "").lower() else "INDIVIDUAL",
    )

    if constants.VERBOSE:
        print(f"\n{'='*80}")
        print("PROJECT SUMMARY - (LLM-based results: summaries)")
        print(f"{'='*80}\n")
        print(f"All insights successfully generated for: {zip_name}.")
        print(f"\n{'='*80}\n")

    return {
        "project_summary": project_summary,
        "contribution_summary": contribution_summary,
    }


def display_code_llm_results(project_name, project_summary, contribution_summary, mode="INDIVIDUAL"):
    print(f"\n[{mode}-CODE] Project: {project_name}")

    print("\n  Project Summary:")
    print(textwrap.fill(project_summary, width=80, subsequent_indent="    "))

    print("\n  Contribution Summary:")
    print(textwrap.fill(contribution_summary, width=80, subsequent_indent="    "))

    print("\n" + "-" * 80 + "\n")


def generate_code_llm_project_summary(project_context: str, readme_tech_ok: bool) -> str:
    """
    Produce a high-level project description (not tied to a single contributor).
    Emphasizes purpose, functionality, and scope — uses README when present.
    """
    if not project_context or not project_context.strip():
        return "[Project summary unavailable: no context found]"

    prompt = f"""
You are describing a software project at a high level for documentation.

Focus ONLY on:
- what the project is for (purpose, goals, and end users)
- what major features or modules exist
- the general technologies/frameworks mentioned
- avoid specific function names or file references

Do NOT:
- mention individual contributors, commits, or versions
- use phrases like "is being developed", "is under development", or "aims to"

Important constraints:
- Use the README as the primary source for purpose and features when present.
- README_TECH_OK indicates whether the README explicitly mentions detected languages or frameworks.
- If README_TECH_OK is False, do not infer technologies from the README; only mention those in TECH STACK.
- Do not mention any technologies not present in TECH STACK or explicitly stated in the README.
- When uncertain, omit the technology rather than guessing.

Format rules:
- Output exactly one plain paragraph.
- No headings, bullet points, numbering, or markdown.
- Do not include labels (e.g., "Project Overview", "Technologies") or inference notes.

README_TECH_OK: {readme_tech_ok}

Context (README if available + TECH STACK + code context):
{project_context[:8000]}

Output one concise paragraph (80–110 words) written in PRESENT TENSE starting with "A project that..." or "An application that...".
"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You write concise, factual project summaries based on technical documentation.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=220,
        )
        return _sanitize_resume_paragraph(completion.choices[0].message.content.strip())
    except Exception as e:
        print(f"Error generating project summary: {e}")
        return "[Project summary unavailable due to API error]"

def generate_code_llm_contribution_summary(project_context):
    """
    Produce a first-person contribution paragraph with implementation detail.
    Focus on what was built, key files, and impact.
    """
    prompt = f"""
You are describing ONE contributor’s personal role in building this project.

Write a short, first-person paragraph (≈80–120 words) covering:
- what I designed or implemented (based on evident code, comments, or structure)
- key technical aspects (libraries, methods, or pipelines actually present)
- the results or impact (performance, usability, automation, etc.)

Be specific to implementation. You may mention code patterns or technologies if visible.
Do NOT restate the high-level project purpose.

Context (from source code & comments):
{project_context[:8000]}

Output one strong paragraph starting with a past-tense action verb (e.g., Implemented, Designed, Developed).
DO NOT begin with "Here's a paragraph" or any sort of preamble and go into the paragrpah directly.
"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise technical résumé writer focusing on contributions "
                        "within collaborative codebases."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.15,
            max_tokens=220,
        )
        raw = completion.choices[0].message.content.strip()
        return _sanitize_resume_paragraph(raw)
    except Exception as e:
        print(f"Error generating contribution summary: {e}")
        return "[Contribution summary unavailable due to API error]"


def _sanitize_resume_paragraph(text: str) -> str:
    # Remove leading role preambles like "As a software developer," / "As an engineer,"
    text = re.sub(r"^\s*As\s+an?\s+[^,]+,\s*", "", text, flags=re.IGNORECASE)

    # Collapse to one clean paragraph
    text = re.sub(r"\s*\n+\s*", " ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()

    # Ensure we don't accidentally start with "As a ..." again
    if re.match(r"^As\s+an?\s", text, flags=re.IGNORECASE):
        text = re.sub(r"^As\s+an?\s+[^,]+,\s*", "", text)

    return text
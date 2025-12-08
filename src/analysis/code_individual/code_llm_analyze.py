import os
import textwrap
import re
from typing import Any, Dict, Optional
from src.utils.helpers import extract_code_file, extract_readme_file, read_file_content
from dotenv import load_dotenv
from groq import Groq
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
    focus_file_paths=None,  # NEW: optional list of file paths to focus on
) -> Optional[Dict[str, Any]]:

    if not isinstance(parsed_files, list):
        return None

    # 1. Select code files
    all_code_files = [f for f in parsed_files if f.get("file_type") == "code"]
    if not all_code_files:
        print("No code files found to analyze.")
        return None

    code_files = all_code_files

    # If we know which files the user actually touched, restrict to those
    if focus_file_paths:
        normalized_focus = [p.replace("\\", "/") for p in focus_file_paths]
        filtered = []

        for f in all_code_files:
            fp = (f.get("file_path") or "").replace("\\", "/")
            # Match if the parsed path *ends with* one of the focus paths
            if any(fp.endswith(target) for target in normalized_focus):
                filtered.append(f)

        if filtered:
            code_files = filtered
            
    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)
        
    if constants.VERBOSE:
        print(f"\n{'='*80}")
        print(f"Analyzing {len(code_files)} file(s) using LLM-based analysis...")
        print(f"{'='*80}\n")
    
    readme_text = extract_readme_file(base_path)
    if readme_text and len(readme_text) > 8000:
        readme_text = readme_text[:8000]

    # We now build TWO contexts:
    #  - project_context_parts: README + code snippets (for project summary)
    #  - contrib_context_parts: code snippets ONLY (for contribution summary)
    project_context_parts: list[str] = []
    contrib_context_parts: list[str] = []

    if readme_text:
        project_context_parts.append(f"README:\n{readme_text}")

    # 2. Build context from code files
    for file_info in code_files:
        file_path = os.path.join(base_path, file_info["file_path"])

        # For focused collaborative analysis, use full file contents.
        # For other cases, keep the lighter "headers + comments" mode.
        if focus_file_paths:
            code_context = read_file_content(file_path)
        else:
            code_context = extract_code_file(file_path)

        if code_context:
            snippet = f"### {file_info['file_name']} ###\n{code_context}"
            project_context_parts.append(snippet)
            contrib_context_parts.append(snippet)

    project_context = "\n\n".join(project_context_parts)
    contribution_context = "\n\n".join(contrib_context_parts)

    if not project_context:
        print("No readable code context found. Skipping LLM analysis.\n")
        return None

    # If somehow no code made it into contrib_context, fall back to project_context
    # (rare; but keeps behaviour from totally breaking).
    if not contribution_context:
        contribution_context = project_context

    # 3. Infer a project name if not provided
    project_folders = sorted(
        set(os.path.dirname(f["file_path"]).split(os.sep)[0] for f in code_files)
    )
    if not project_name:
        project_name = project_folders[0] if project_folders else zip_name

    # 4. Call the existing LLM helpers
    #    - Project summary: README + light code context
    #    - Contribution summary: CODE-ONLY context (no README content)
    project_summary = generate_code_llm_project_summary(readme_text)
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
    

def generate_code_llm_project_summary(readme_text):
    """
    Produce a high-level project description (not tied to a single contributor).
    Emphasizes purpose, functionality, and scope — uses README primarily.
    """
    if not readme_text:
        readme_text = "No README content was found for this project."

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

Use the README as the main source.

README:
{readme_text[:5000]}

Output one concise paragraph (80–100 words) written in PRESENT TENSE starting with "A project that..." or "An application that...".
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
            max_tokens=180,
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



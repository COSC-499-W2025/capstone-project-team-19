import os
import textwrap
import re
from src.helpers import extract_code_file, extract_readme_file
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def run_code_llm_analysis(parsed_files, zip_path):    
    if not isinstance(parsed_files, list):
        return
        
    code_files = [f for f in parsed_files if f.get("file_type") == "code"]
    if not code_files:
        print("No code files found to analyze.")
        return
        
    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)
        
    print(f"\n{'='*80}")
    print(f"Analyzing {len(code_files)} file(s) using LLM-based analysis...")
    print(f"{'='*80}\n")
    
    readme_text = extract_readme_file(base_path)
    
    # trim super long readme files
    if readme_text and len(readme_text) > 8000:
        readme_text = readme_text[:8000]
    
    project_context_parts = []

    if readme_text:
        project_context_parts.append(f"README:\n{readme_text}")

    for file_info in code_files:
        file_path = os.path.join(base_path, file_info["file_path"])
        code_context = extract_code_file(file_path)
        if code_context:
            project_context_parts.append(f"### {file_info['file_name']} ###\n{code_context}")

    project_context = "\n\n".join(project_context_parts)
    if not project_context:
        print("No readable code context found. Skipping LLM analysis.\n")
        return
    
    # get the top-level folder name where the code files live
    project_folders = sorted(set(os.path.dirname(f["file_path"]).split(os.sep)[0] for f in code_files))
    project_name = project_folders[0] if project_folders else zip_name
    
    summary = generate_code_llm_summary(project_context)
    display_code_llm_results(project_name, summary)
        
    print(f"\n{'='*80}")
    print("PROJECT SUMMARY - (LLM-based results: summaries)")
    print(f"{'='*80}\n")
    print(f"All insights successfully generated for: {zip_name}.")
    print(f"\n{'='*80}\n")


def display_code_llm_results(project_name, summary):
    print(f"Project: {project_name}")
    print("\n  Summary:")
    print(textwrap.fill(summary, width=80, subsequent_indent="    "))
    print("\n" + "-"*80 + "\n")

    

def generate_code_llm_summary(project_context):
    """
    Produce ONE first-person, resume-ready paragraph (≈80–120 words)
    with this flow: purpose → what I built/did → real tech used → impact.
    Start with a strong past-tense action verb (Built/Developed/Designed/Implemented).
    """
    prompt = f"""
You are a technical résumé writer. Based ONLY on the provided context (README + headers/docstrings/comments),
write ONE concise paragraph (80–120 words) in FIRST PERSON ("I ...") that follows this flow:
- the project's purpose and what it enables,
- what I specifically designed/implemented/tested/optimized,
- the key technologies/patterns that are actually evident in the context,
- the impact for users or stakeholders (performance, reliability, usability, insight).

Style rules (must follow):
- Start the paragraph with a strong past-tense action verb (e.g., Built, Developed, Designed, Implemented).
- Do NOT use bullets, numbering, headings, or markdown.
- Do NOT list file or function names (refer generically, e.g., "the application", "the pipeline").
- Do NOT invent libraries or tools that are not present in the context.
- Professional, concrete, impact-oriented tone. One paragraph only.

Context:
{project_context[:12000]}

Output: one paragraph, first person, 80–120 words, starting with a past-tense action verb.
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise technical résumé writer. "
                        "Always return one first-person paragraph (no lists/markdown). "
                        "Mention only technologies present in the provided context."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.15,   # tighter for consistency
            max_tokens=220,
        )
        raw = completion.choices[0].message.content.strip()
        return _sanitize_resume_paragraph(raw)
    except Exception as e:
        print(f"Error generating project summary: {e}")
        return "[Summary unavailable due to API error]"
    

def _sanitize_resume_paragraph(text: str) -> str:
    # Remove leading role preambles like "As a software developer," / "As an engineer,"
    text = re.sub(r"^\s*As\s+an?\s+[^,]+,\s*", "", text, flags=re.IGNORECASE)

    # Remove explicit file names (main.cpp, data_utils.py, index.html, style.css, sensor.h, etc.)
    text = re.sub(r"\b[\w\-]+\.(?:py|js|cpp|c|h|html|css|java)\b", "the codebase", text)

    # Replace identifier-y tokens with generic phrasing (softly)
    text = re.sub(r"\b[a-z]+(?:_[a-z0-9]+)+\b", "a utility function", text)      # snake_case
    text = re.sub(r"\b[a-z]+[A-Z][a-zA-Z0-9]*\b", "a utility function", text)    # camelCase

    # Collapse to one clean paragraph
    text = re.sub(r"\s*\n+\s*", " ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()

    # Ensure we don't accidentally start with "As a ..." again
    if re.match(r"^As\s+an?\s", text, flags=re.IGNORECASE):
        text = re.sub(r"^As\s+an?\s+[^,]+,\s*", "", text)

    return text


import os
import textwrap
from helpers import extract_code_file, extract_readme_file
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
    
    summary = generate_code_llm_summary(project_context)
    display_code_llm_results(zip_name, summary)
        
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
    prompt = f"""
    You are analyzing a multi-file software project.

    Based on the following combined content (including README excerpts,
    function/class headers, comments, and docstrings), write a clear,
    technical summary describing:
      1. What the project does (overall purpose)
      2. Its main features or modules
      3. The technologies, algorithms, or design patterns it uses
      4. Its potential applications or intended users

    Keep your response under 150 words, in a professional and concise tone.

    Combined project context:
    {project_context[:12000]}

    Your summary:
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a technical analyst who summarizes software projects "
                        "based on code structure and documentation. "
                        "Your tone should be precise, neutral, and professional."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=250,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating project summary: {e}")
        return "[Summary unavailable due to API error]"


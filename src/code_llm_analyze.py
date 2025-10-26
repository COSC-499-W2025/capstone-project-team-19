import os
import textwrap
from helpers import extract_code_file
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
        
    total_files = len(code_files)
    for idx, file_info in enumerate(code_files, start=1):
        file_path = os.path.join(base_path, file_info["file_path"])
        filename = file_info["file_name"]
        print(f"[{idx}/{total_files}] Processing: {filename}")
    
        code = extract_code_file(file_path)
        if not code:
            print(f"Skipping {filename}: failed to extract text.\n")
            continue
    
        summary = generate_code_llm_summary(code)
        display_code_llm_results(filename, summary)
        
    print(f"\n{'='*80}")
    print("PROJECT SUMMARY - (LLM-based results: summaries, skills, and success factors)")
    print(f"{'='*80}\n")
    print("All insights successfully generated for eligible text files.")
    print(f"\n{'='*80}\n")


def display_code_llm_results(filename, summary):
    print(f"Processing: {filename}")
    print("\n  Summary:")
    print(textwrap.fill(summary, width=80, subsequent_indent="    "))
    

def generate_code_llm_summary(code):
    prompt = (
        
    )
    return True


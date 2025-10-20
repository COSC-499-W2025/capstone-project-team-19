import os

def run_llm_analysis(parsed_files, zip_path):
    if not isinstance(parsed_files, list):
        return

    text_files = [f for f in parsed_files if f.get("file_type") == "text"]
    if not text_files:
        print("No text files found to analyze.")
        return

    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)

    print(f"\n{'='*80}")
    print(f"Analyzing {len(text_files)} file(s) using LLM-based analysis...")
    print(f"{'='*80}\n")

    for file_info in text_files:
        file_path = os.path.join(base_path, file_info["file_path"])
        filename = file_info["file_name"]

        print(f"Processing: {filename}")
        print(f"  [LLM placeholder] Extracting insights from {filename}...\n")

    print(f"\n{'='*80}")
    print("PROJECT SUMMARY - (LLM-based results placeholder)")
    print(f"{'='*80}\n")
    print("This is where aggregated metrics from the LLM will appear once integrated.")
    print(f"\n{'='*80}\n")

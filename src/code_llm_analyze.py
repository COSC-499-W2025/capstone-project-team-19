import os
import textwrap
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def run_code_llm_analysis(parsed_files, zip_path):
    print("\nYou are running a code analysis using LLM")
    return True

def display_code_llm_results(filename, summary):
    print("\nHere is your summary")
    return True

def generate_code_llm_summary(code):
    print("\nAnalysing code file and getting summary...")
    return True


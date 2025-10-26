import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def run_code_llm_analysis(parsed_files, zip_path):
    print("You are running a code analysis using LLM")
    return True
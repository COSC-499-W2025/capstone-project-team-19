import os
import textwrap
from alt_analyze import analyze_linguistic_complexity, extractfile
from groq import Groq  # make sure groq is installed

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def run_llm_analysis(parsed_files, zip_path):
    """Run the LLM-based text analysis pipeline (summary only for now)."""
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

        text = extractfile(file_path)
        if not text:
            print(f"Skipping {filename}: failed to extract text.\n")
            continue

        # linguistic baseline
        linguistic = analyze_linguistic_complexity(text)

        # LLM-generated summary
        summary = generate_llm_summary(text)

        # placeholders for later
        skills = ["None"]
        success = {"strengths": "None", "weaknesses": "None", "score": "None"}

        display_llm_results(filename, linguistic, summary, skills, success)

    print(f"\n{'='*80}")
    print("PROJECT SUMMARY - (LLM-based results: summaries only)")
    print(f"{'='*80}\n")
    print("Summaries successfully generated for eligible text files.")
    print(f"\n{'='*80}\n")


def display_llm_results(filename, linguistic, summary, skills, success):
    print(f"Processing: {filename}")
    print("  Linguistic & Readability:")
    print(f"    Word Count: {linguistic['word_count']}, Sentences: {linguistic['sentence_count']}")
    print(f"    Reading Level: {linguistic['reading_level']} (Grade {linguistic['flesch_kincaid_grade']})")
    print(f"    Lexical Diversity: {linguistic['lexical_diversity']}")

    print("\n  Summary:")
    print(textwrap.fill(summary, width=80, subsequent_indent="    "))

    print("\n  Skills Demonstrated:")
    for skill in skills:
        print(f"    - {skill}")

    print("\n  Success Factors:")
    print(f"    Strengths: {success['strengths']}")
    print(f"    Weaknesses: {success['weaknesses']}")
    print(f"    Overall Evaluation: {success['score']}\n")


def generate_llm_summary(text):
    """Use Llama 3.1 (Groq) to summarize text in 3–4 sentences."""
    # safeguard: trim overly long inputs
    text = text[:6000]  # basic cutoff for now
    prompt = (
        "Summarize the following text in 3–4 sentences. "
        "Focus on the main ideas, arguments, and themes:\n\n"
        f"{text}"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful academic summarization assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2, # 0.2 is a good temperature usually used in research (it keeps it near consistent but also has some room for creativity)
            max_tokens=300,
        )
        summary = completion.choices[0].message.content.strip()
        return summary or "[LLM returned empty summary]"
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "[Summary unavailable due to API error]"

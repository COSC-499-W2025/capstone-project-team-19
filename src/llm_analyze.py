import os
import textwrap
from alt_analyze import analyze_linguistic_complexity, extractfile
from dotenv import load_dotenv
from groq import Groq
from tqdm import tqdm

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


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

    for file_info in tqdm(text_files, desc="Processing files", unit="file"):
        file_path = os.path.join(base_path, file_info["file_path"])
        filename = file_info["file_name"]

        text = extractfile(file_path)
        if not text:
            print(f"Skipping {filename}: failed to extract text.\n")
            continue

        # baseline metrics
        linguistic = analyze_linguistic_complexity(text)

        # LLM calls
        summary = generate_llm_summary(text)
        skills = generate_llm_skills(text)
        success = generate_llm_success_factors(text, linguistic)

        display_llm_results(filename, linguistic, summary, skills, success)

    print(f"\n{'='*80}")
    print("PROJECT SUMMARY - (LLM-based results: summaries, skills, and success factors)")
    print(f"{'='*80}\n")
    print("All insights successfully generated for eligible text files.")
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
    text = text[:6000]
    prompt = (
        "You are analyzing a document that could be any type of written work — "
        "such as an essay, research paper, project proposal, creative writing, reflection, or script.\n\n"
        "Step 1: Identify what kind of document this most likely is (e.g., 'research essay', 'creative story', 'project proposal', 'script').\n"
        "Step 2: In ONE clear, formal sentence, describe the document’s *purpose* — "
        "what the author or creator is trying to achieve, examine, express, or demonstrate.\n\n"
        "Write your output in this format (no labels, just plain text):\n"
        "A [document type] that [purpose summary].\n\n"
        f"Text:\n{text}\n\n"
        "Your response:"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise academic and creative writing classifier. "
                        "You infer both the document type and its purpose in a concise, formal tone."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.25,
            max_tokens=150,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "[Summary unavailable due to API error]"


def generate_llm_skills(text):
    text = text[:6000]
    prompt = (
        "From the following text, infer 3–5 key *skills* demonstrated by the author or creator. "
        "Think broadly — the text might show analytical reasoning, storytelling, design thinking, data analysis, "
        "communication, project planning, teamwork, or creativity. "
        "Write each skill as a short phrase suitable for a résumé (no numbering, just bullet-style lines).\n\n"
        f"Text:\n{text}\n\n"
        "Output example:\n"
        "- Analytical reasoning and synthesis\n"
        "- Structured argumentation and clarity\n"
        "- Creative expression through dialogue\n\n"
        "Now list the most relevant skills:"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You identify and phrase professional or academic skills demonstrated through written work. "
                        "Keep them concise and skill-oriented."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )
        raw_output = completion.choices[0].message.content.strip()
        skills = [
            line.lstrip("-• ").strip()
            for line in raw_output.split("\n")
            if line.strip()
        ]
        return skills[:5] if skills else ["None"]
    except Exception as e:
        print(f"Error generating skills: {e}")
        return ["[Skills unavailable due to API error]"]


def generate_llm_success_factors(text, linguistic):
    """Generate concise, context-aware success factors that adapt to different text types."""
    text = text[:6000]
    readability = linguistic.get("reading_level", "N/A")
    diversity = linguistic.get("lexical_diversity", "N/A")
    word_count = linguistic.get("word_count", "N/A")

    prompt = (
        f"You are evaluating a piece of writing. Here are some details:\n"
        f"- Reading level: {readability}\n"
        f"- Lexical diversity: {diversity}\n"
        f"- Word count: {word_count}\n\n"
        "Different kinds of text require different evaluation criteria:\n"
        "- Academic or analytical works → clarity of argument, evidence use, structure, originality.\n"
        "- Creative or narrative works → storytelling, emotional depth, imagery, originality.\n"
        "- Functional or professional texts (e.g., project proposals, itineraries, reports, resumes) → clarity, organization, tone, usefulness, professionalism.\n\n"
        "Tailor your assessment accordingly.\n\n"
        "Write three brief parts:\n"
        "1. **Strengths:** 2–4 short, specific phrases (no full sentences).\n"
        "2. **Weaknesses:** 2–4 short, specific phrases (avoid generic terms like 'needs improvement').\n"
        "3. **Overall Evaluation:** Give a score from 1 to 10, with a 3–5 word summary in parentheses "
        "(e.g., '8.3 / 10 (Strong clarity)').\n\n"
        "Keep the total response under 30 words and respond *only* in JSON format like this:\n"
        "{\n"
        '  "strengths": "clear layout, consistent tone, relevant examples",\n'
        '  "weaknesses": "minor redundancy, limited depth",\n'
        '  "score": "8.1 / 10 (Well-organized work)"\n'
        "}\n\n"
        f"Text:\n{text}\n\n"
        "Your response:"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise evaluator who adapts your judgment based on the document type. "
                        "Avoid repeating stock phrases and keep the tone professional."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.45,
            max_tokens=200,
        )

        import json
        raw_output = completion.choices[0].message.content.strip()

        try:
            data = json.loads(raw_output)
            return {
                "strengths": data.get("strengths", "None"),
                "weaknesses": data.get("weaknesses", "None"),
                "score": data.get("score", "None"),
            }
        except json.JSONDecodeError:
            return {
                "strengths": "[Parsing error: raw output below]",
                "weaknesses": raw_output,
                "score": "None",
            }

    except Exception as e:
        print(f"Error generating success factors: {e}")
        return {"strengths": "None", "weaknesses": "None", "score": "None"}


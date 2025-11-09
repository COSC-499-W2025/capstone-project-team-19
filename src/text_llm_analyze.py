import os
import textwrap
import json
from src.alt_analyze import analyze_linguistic_complexity
from src.helpers import extract_text_file
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def run_text_llm_analysis(parsed_files, zip_path, conn, user_id):
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

    # group text files by project folder name
    projects = {}
    for f in text_files:
        if not f.get("file_path"):
            continue
        project_name = f["file_path"].split(os.sep)[0]
        projects.setdefault(project_name, []).append(f)

    # process each folder as one project
    for project_name, files in projects.items():
        print(f"\n→ {project_name}")
        files_sorted = sorted(files, key=lambda x: x["file_name"])

        # ask user to identify main file
        if len(files_sorted) == 1:
            main_file = files_sorted[0]
            print(f"Only one text file detected: {main_file['file_name']}")
        else:
            print("\nSelect the MAIN (final) file for this project:")
            for idx, f in enumerate(files_sorted, start=1):
                print(f"  {idx}. {f['file_name']}")
            choice = input("Enter number of main file (or press Enter to auto-select largest): ").strip()

            if choice.isdigit() and 1 <= int(choice) <= len(files_sorted):
                main_file = files_sorted[int(choice) - 1]
            else:
                # fallback: pick largest file by size
                main_file = max(
                    files_sorted,
                    key=lambda f: os.path.getsize(os.path.join(base_path, f["file_path"]))
                )
                print(f"Auto-selected: {main_file['file_name']}")

        main_path = os.path.join(base_path, main_file["file_path"])
        main_text = extract_text_file(main_path, conn, user_id)
        if not main_text:
            print("Failed to extract main file text. Skipping project.\n")
            continue
        
        # gather supporting text (outlines, drafts, etc)
        supporting_files = [f for f in files_sorted if f != main_file]
        supporting_texts = []
        for f in supporting_files:
            path = os.path.join(base_path, f["file_path"])
            text_content = extract_text_file(path, conn, user_id)
            if text_content:  # skip empty extractions
                supporting_texts.append({
                    "filename": f.get("file_name", "Unknown File"),
                    "text": text_content
                })


        print(f"  Found {len(supporting_texts)} supporting file(s).")

        # baseline metrics
        linguistic = analyze_linguistic_complexity(main_text)

        # LLM calls
        summary = generate_text_llm_summary(main_text)
        skills = generate_text_llm_skills(main_text, supporting_texts)
        success = generate_text_llm_success_factors(main_text, linguistic, supporting_texts)

        display_text_llm_results(project_name, main_file["file_name"], linguistic, summary, skills, success)

    print(f"\n{'='*80}")
    print("PROJECT SUMMARY - (LLM-based results: summaries, skills, and success factors)")
    print(f"{'='*80}\n")
    print("All insights successfully generated for eligible text projects.")
    print(f"\n{'='*80}\n")


def display_text_llm_results(project_name, main_file_name, linguistic, summary, skills, success):
    print(f"\nProject: {project_name}")
    print(f"[Main File] {main_file_name}")
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
    
    # format strengths and weaknesses nicely
    def print_list_or_str(label, content):
        print(f"    {label}:")
        if isinstance(content, list):
            for item in content:
                print(f"      - {item}")
        elif isinstance(content, str):
            # Handle case where LLM returns comma-separated strings
            if content.startswith("[") and content.endswith("]"):
                try:
                    parsed = json.loads(content)
                    for item in parsed:
                        print(f"      - {item}")
                except Exception:
                    print(f"      {content}")
            elif "," in content:
                for part in [x.strip() for x in content.split(",") if x.strip()]:
                    print(f"      - {part}")
            else:
                print(f"      - {content}")
        else:
            print(f"      - {str(content)}")

    print_list_or_str("Strengths", success.get("strengths", "None"))
    print_list_or_str("Weaknesses", success.get("weaknesses", "None"))
    print(f"    Overall Evaluation: {success.get('score', 'None')}\n")


def generate_text_llm_summary(text):
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


def generate_text_llm_skills(main_text, supporting_texts=None):
    main_text = main_text[:6000]
    merged_supporting = ""

    if supporting_texts:
        for s in supporting_texts:
            merged_supporting += f"\n\n### {s['filename']} ###\n{s['text'][:1500]}"
            
    prompt = (
        "You are analyzing a writing project composed of a main document and optional supporting materials "
        "(e.g., outlines, drafts, notes, reflections). Together they demonstrate both writing skill and process.\n\n"
        "Step 1: Consider the main document as the final polished work — it shows core writing quality, clarity, and organization.\n"
        "Step 2: Consider the supporting materials as evidence of process skills — planning, structuring ideas, research, or revision.\n\n"
        "Infer 3–6 résumé-ready skills that the author demonstrates across all materials. "
        "Be concrete and skill-oriented (e.g., 'Analytical reasoning', 'Structured argumentation', 'Creative development', "
        "'Research synthesis', 'Iterative editing and reflection').\n\n"
        "Output one skill per line (no numbering, no extra text).\n\n"
        "MAIN DOCUMENT:\n"
        f"{main_text}\n\n"
        "SUPPORTING MATERIALS:\n"
        f"{merged_supporting}\n\n"
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
                        "taking into account both final work and process evidence."
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


def generate_text_llm_success_factors(main_text, linguistic, supporting_texts=None):
    main_text = main_text[:6000]
    readability = linguistic.get("reading_level", "N/A")
    diversity = linguistic.get("lexical_diversity", "N/A")
    word_count = linguistic.get("word_count", "N/A")

    merged_supporting = ""
    if supporting_texts:
        for s in supporting_texts:
            merged_supporting += f"\n\n### FILE: {s['filename']} ###\n{s['text'][:1200]}"

    prompt = (
        "You are evaluating a complete writing project that includes both a final document "
        "and supporting materials such as outlines, drafts, and notes. "
        "The final document shows end quality, while the supporting files reveal process, planning, and revision.\n\n"
        f"Here are metrics from the main document:\n"
        f"- Reading level: {readability}\n"
        f"- Lexical diversity: {diversity}\n"
        f"- Word count: {word_count}\n\n"
        "Assess both the final quality *and* the creative or analytical process using these criteria:\n"
        "- Clarity and organization in the final text\n"
        "- Depth of ideas and originality\n"
        "- Writing craftsmanship (tone, coherence, structure)\n"
        "- Evidence of iteration, planning, or critical reflection in supporting materials\n\n"
        "When mentioning any strength or weakness that clearly relates to a supporting file, "
        "include the exact filename in parentheses ONLY IF THEY EXIST. "
        "Do NOT use vague phrases like 'in supporting files' or 'in drafts' — always specify the file name if available AND ONLY IF AVAILABLE.\n\n"
        "Write your response in clean JSON with three fields:\n"
        "{\n"
        '  \"strengths\": [\"3–5 concise phrases (≤8 words each)\"],\n'
        '  \"weaknesses\": [\"3–5 concise phrases (≤8 words each)\"],\n'
        '  \"score\": \"score like 8.4 / 10 (clear process and quality)\"\n'
        "}\n\n"
        "Keep total response under 50 words. Avoid full sentences, markdown, or bullet formatting.\n\n"
        f"MAIN DOCUMENT:\n{main_text}\n\n"
        f"SUPPORTING MATERIALS:\n{merged_supporting}\n\n"
        "Your response:"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an academic evaluator who assesses both final writing quality and process evidence. "
                        "Respond only in clean JSON (no markdown or commentary)."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.45,
            max_tokens=250,
        )

        raw = completion.choices[0].message.content.strip()

        # Clean markdown fences
        if "```" in raw:
            parts = raw.split("```")
            raw = max(parts, key=len)

        # Remove stray headers
        raw = "\n".join(
            line for line in raw.splitlines()
            if not line.strip().startswith(("###", "**", "Final", "Part", "json"))
        ).strip()

        # Extract JSON substring
        if "{" in raw and "}" in raw:
            raw = raw[raw.find("{") : raw.rfind("}") + 1]

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print("\n Could not parse model response:\n", raw[:500])
            raise

        return {
            "strengths": data.get("strengths", "None"),
            "weaknesses": data.get("weaknesses", "None"),
            "score": data.get("score", "None"),
        }

    except Exception as e:
        print(f"Error generating success factors: {e}")
        return {"strengths": "None", "weaknesses": "None", "score": "None"}


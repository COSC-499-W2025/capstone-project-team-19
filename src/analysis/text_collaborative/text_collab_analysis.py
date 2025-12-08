import re
import textwrap
from src.analysis.text_individual.text_analyze import run_text_pipeline
from src.analysis.text_individual.llm_summary import generate_text_llm_summary, generate_contribution_llm_summary
from src.analysis.text_individual.alt_summary import prompt_manual_summary
from src.analysis.skills.flows.text_skill_extraction import extract_text_skills
from src.utils.helpers import normalize_pdf_paragraphs
from src.db import get_files_with_timestamps, get_classification_id, store_text_activity_contribution
from src.analysis.activity_type.text.activity_type import print_activity, get_activity_contribution_data
try:
    from src import constants
except ModuleNotFoundError:
    import constants

def analyze_collaborative_text_project(
    conn,
    user_id,
    project_name,
    parsed_files,
    zip_path,
    external_consent,
    summary_obj  # ProjectSummary instance
):
    """
    Collaborative TEXT project analysis flow.
    1. Run full text pipeline (main summary, CSV metadata).
    2. Ask user which sections they personally wrote.
    3. Extract contributed text.
    4. Summarize their contribution (LLM or manual).
    5. Run skill detectors on *only contributed text*.
    6. Save structured output to summary.contributions["text_collab"].
    """

    if constants.VERBOSE:
        print("\n[TEXT-COLLAB] Starting collaborative text analysis…")

    # ---------------------------------------------------------
    # STEP 1 — Run main pipeline to get the full summary + skills
    # ---------------------------------------------------------
    pipeline_result = run_text_pipeline(
        parsed_files=parsed_files,
        zip_path=zip_path,
        conn=conn,
        user_id=user_id,
        project_name=project_name,
        consent=external_consent,
        suppress_print=True
    )

    if not pipeline_result:
        print("[TEXT-COLLAB] No pipeline output. Skipping.")
        return

    # pipeline_result contains:
    #  {
    #    "project_summary": ...
    #    "skills": ...
    #    "buckets": ...
    #    "overall_score": ...
    #    "main_file": "filename"
    #  }

    main_file_name = pipeline_result["main_file"]
    full_main_text = _load_main_text(parsed_files, main_file_name, zip_path, conn, user_id)

    # Normalize full document (fixes broken PDF line breaks)
    normalized = normalize_pdf_paragraphs(full_main_text)

    # Recombine normalized paragraphs into a clean text block
    full_main_text = "\n\n".join(normalized)

    # store main summary and skills in project_summary
    summary_obj.summary_text = pipeline_result["project_summary"]
    summary_obj.skills = pipeline_result.get("skills", [])

    print("\n" + "="*80)
    print("MAIN DOCUMENT SUMMARY:")
    print(textwrap.fill(pipeline_result["project_summary"], width=80, subsequent_indent="  "))
    print("="*80 + "\n")

    # ---------------------------------------------------------
    # STEP 2 — Extract sections or paragraphs for user selection
    # ---------------------------------------------------------
    sections = _extract_document_sections(full_main_text)

    print("\nSelect the sections/paragraphs YOU contributed to:")
    for i, sec in enumerate(sections, start=1):
        preview = sec["header"] if sec["header"] else sec["preview"]
        print(f"  {i}. {preview}")

    selected = input(
        "\nEnter the numbers (comma-separated) of the sections you worked on: "
    ).strip()

    if not selected:
        print("[TEXT-COLLAB] No sections selected; assuming 0 contribution.")
        summary_obj.contributions["text_collab"] = {
            "contributed_text": "",
            "percent_of_document": 0,
            "contribution_summary": "[No contributions provided]",
            "skills": {},
            "buckets": {},
            "overall_score": 0
        }
        return

    indices = []
    for x in selected.split(","):
        x = x.strip()
        if not x.isdigit():
            print(f"[Warning] Ignoring invalid input: '{x}'")
            continue

        n = int(x)
        if 1 <= n <= len(sections):
            indices.append(n)
        else:
            print(f"[Warning] Selection {n} is out of range.")

    user_sections = [sections[i - 1] for i in indices]


    contributed_text = "\n\n".join(s["text"] for s in user_sections)
    
    # ---------------------------------------------------------
    # STEP 2B — Ask which SUPPORTING TEXT files they contributed to
    # ---------------------------------------------------------
    supporting_text_files = [
        f for f in parsed_files
        if f["file_type"] == "text"
        and not f["file_name"].lower().endswith(".csv")
        and f["file_name"] != main_file_name
    ]


    supporting_csv_files = [
        f for f in parsed_files
        if f["file_name"].lower().endswith(".csv")
    ]

    # ---- SUPPORTING TEXT FILES ----
    if supporting_text_files:
        print("\nWhich supporting TEXT files did you contribute to?")
        for idx, f in enumerate(supporting_text_files, start=1):
            print(f"  {idx}. {f['file_name']}")
        print("Enter numbers (comma-separated), or 0 for NONE.")

        resp = input("> ").strip()

        text_support_indices = []
        for x in resp.split(","):
            x = x.strip()
            if not x.isdigit():
                print(f"[Warning] Ignoring invalid input: '{x}'")
                continue
            n = int(x)
            if n == 0:
                break
            if 1 <= n <= len(supporting_text_files):
                text_support_indices.append(n)
            else:
                print(f"[Warning] Selection {n} is out of range.")

        selected_text_support_files = [
            supporting_text_files[i - 1] for i in text_support_indices
        ]
    else:
        print("\n(No supporting text files detected.)")
        selected_text_support_files = []


    # ---------------------------------------------------------
    # STEP 2C — Load ENTIRE CONTENT + build structures for detectors
    # ---------------------------------------------------------
    contributed_supporting_texts = []
    supporting_structured = []   # <── NEW (this is what detectors need)

    for f in selected_text_support_files:
        support_text = _load_main_text(parsed_files, f["file_name"], zip_path, conn, user_id)
        normalized_sup = normalize_pdf_paragraphs(support_text)
        clean_text = "\n\n".join(normalized_sup)

        contributed_supporting_texts.append(clean_text)

        # Build structured record for skill detectors
        supporting_structured.append({
            "filename": f["file_name"],
            "text": clean_text
        })


    # ---------------------------------------------------------
    # STEP 2D — CSV selection
    # ---------------------------------------------------------
    if supporting_csv_files:
        print("\nWhich CSV files did you contribute to?")
        for idx, csv_f in enumerate(supporting_csv_files, start=1):
            print(f"  {idx}. {csv_f['file_name']}")
        print("Enter numbers (comma-separated), or 0 for NONE.")

        resp_csv = input("> ").strip()

        csv_support_indices = []
        for x in resp_csv.split(","):
            x = x.strip()
            if not x.isdigit():
                print(f"[Warning] Ignoring invalid input: '{x}'")
                continue
            n = int(x)
            if n == 0:
                break
            if 1 <= n <= len(supporting_csv_files):
                csv_support_indices.append(n)
            else:
                print(f"[Warning] Selection {n} is out of range.")

        user_csv_metadata = None
        if csv_support_indices:
            all_csv_metadata = pipeline_result.get("csv_metadata", {})
            files_metadata = all_csv_metadata.get("files", [])
            user_csv_metadata = {
                "files": [
                    files_metadata[i - 1]
                    for i in csv_support_indices
                    if i - 1 < len(files_metadata)
                ]
            }
    else:
        print("\n(No CSV files detected.)")
        user_csv_metadata = None


    # ---------------------------------------------------------
    # MERGE ALL CONTRIBUTED TEXT
    # ---------------------------------------------------------
    contributed_text = (
        contributed_text + "\n\n" + "\n\n".join(contributed_supporting_texts)
    )

    # ---------------------------------------------------------
    # STEP 2E — Activity Type Analysis for Contributed Files
    # ---------------------------------------------------------
    # Build list of file names the user contributed to
    contributed_file_names = [main_file_name]  # always include main file
    contributed_file_names.extend([f["file_name"] for f in selected_text_support_files])

    # If user contributed to CSV files, add them too
    if user_csv_metadata and user_csv_metadata.get('files'):
        contributed_file_names.extend([
            csv_file.get('file_name')
            for csv_file in user_csv_metadata['files']
        ])

    # Fetch timestamp data for ALL project files
    all_project_files = get_files_with_timestamps(conn, user_id, project_name)

    # Filter to only files the user contributed to
    user_contributed_files = [
        f for f in all_project_files
        if f.get("file_name") in contributed_file_names
    ]

    # Generate activity type data for user's contributed files
    if user_contributed_files:
        print_activity(user_contributed_files, project_name, main_file_name=main_file_name)

        # Store activity type data to database
        activity_data = get_activity_contribution_data(user_contributed_files, main_file_name=main_file_name)
        classification_id = get_classification_id(conn, user_id, project_name)
        if classification_id:
            store_text_activity_contribution(conn, classification_id, activity_data)

    # ---------------------------------------------------------
    # STEP 3 — Compute % of contribution
    # ---------------------------------------------------------
    user_wc = len(contributed_text.split())
    total_wc = len(full_main_text.split())
    pct = round((user_wc / total_wc) * 100, 2) if total_wc > 0 else 0

    # ---------------------------------------------------------
    # STEP 4 — FIRST-PERSON contribution summary
    # ---------------------------------------------------------
    if external_consent == "accepted":
        contribution_summary = generate_contribution_llm_summary(
            full_main_text, contributed_text
        )
    else:
        contribution_summary = _manual_contribution_summary_prompt()

    if constants.VERBOSE:
        print("\n" + "="*80)
    print("YOUR CONTRIBUTION SUMMARY:")
    print(textwrap.fill(contribution_summary, width=80, subsequent_indent="  "))
    if constants.VERBOSE:
        print("="*80 + "\n")

    # ---------------------------------------------------------
    # STEP 5 — Run skill detectors on ONLY the contributed text
    # ---------------------------------------------------------
    skill_output = extract_text_skills(
        main_text=contributed_text,
        supporting_texts=supporting_structured,
        csv_metadata=user_csv_metadata,
        project_name=project_name,
        user_id=user_id,
        conn=conn,
    )

    # ---------------------------------------------------------
    # STEP 6 — Store in project summary
    # ---------------------------------------------------------
    # Store buckets without evidence to reduce size (evidence contains verbose CSV metadata)
    buckets_clean = {}
    for bucket_name, bucket_data in skill_output.get("buckets", {}).items():
        buckets_clean[bucket_name] = {
            "description": bucket_data.get("description"),
            "score": bucket_data.get("score")
        }
    
    summary_obj.contributions["text_collab"] = {
        "percent_of_document": pct,
        "contribution_summary": contribution_summary,
        "skills": skill_output.get("skills", []),
        "buckets": buckets_clean,
        "overall_score": skill_output.get("overall_score")
    }
    
    # Print the skill detector output for the user
    print("\nSkill Scores:")
    print("-" * 60)
    for bucket, data in skill_output.get("buckets", {}).items():
        print(f"{bucket:20s}  score={data['score']:.2f}   ({data['description']})")
    print("-" * 60)
    print(f"OVERALL SCORE: {skill_output.get('overall_score'):.2f}")
    print("-" * 60)


    print("[TEXT-COLLAB] Collaborative text analysis complete.")


# ------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------

def _load_main_text(parsed_files, main_file_name, zip_path, conn, user_id):
    """Load the main file content using extract_text_file."""
    from src.utils.helpers import extract_text_file
    import os

    # find file entry
    match = next((f for f in parsed_files if f["file_name"] == main_file_name), None)
    if not match:
        return ""

    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)

    path = os.path.join(base_path, match["file_path"])
    return extract_text_file(path, conn, user_id) or ""


def _extract_document_sections(full_text: str):
    """
    Detect headers OR paragraph previews.
    Return list of {header, preview, text}.
    """

    lines = full_text.split("\n")
    sections = []
    buffer = []
    current_header = None

    header_pattern = re.compile(r"^[A-Z][A-Za-z ]{2,}$")  # e.g. "Introduction", "Method"

    for line in lines:
        stripped = line.strip()

        if header_pattern.match(stripped):  # header detected
            # flush previous section
            if buffer:
                section_text = "\n".join(buffer).strip()
                sections.append({
                    "header": current_header,
                    "preview": section_text[:60],
                    "text": section_text
                })
                buffer = []

            current_header = stripped
        else:
            buffer.append(stripped)

    # flush last
    if buffer:
        section_text = "\n".join(buffer).strip()
        sections.append({
            "header": current_header,
            "preview": section_text[:60],
            "text": section_text
        })

    # If NO headers at all → use paragraph previews
    if all(s["header"] is None for s in sections):
        paragraphs = [p.strip() for p in full_text.split("\n") if p.strip()]
        sections = []
        for p in paragraphs:
            preview = " ".join(p.split()[:5])
            sections.append({
                "header": None,
                "preview": preview + "...",
                "text": p
            })

    return sections


def _manual_contribution_summary_prompt():
    """Manual first-person contribution statement."""
    print("\nLLM consent not granted. Please describe your contributions.\n")
    print("What types of contribution did you make?")
    options = [
        "Writing", "Editing", "Research", "Formatting",
        "Proofreading", "Data Analysis", "Drafting", "Revising"
    ]
    for i, opt in enumerate(options, start=1):
        print(f"{i}. {opt}")

    nums = input("Enter numbers (comma-separated): ").strip()
    selected = [options[int(n.strip()) - 1] for n in nums.split(",") if n.strip().isdigit()]

    if not selected:
        return "I contributed to the project, but did not specify the type of work."

    joined = ", ".join(selected)
    return f"I contributed by {joined.lower()}."

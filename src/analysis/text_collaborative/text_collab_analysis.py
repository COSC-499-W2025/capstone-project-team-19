import re
import textwrap
from src.analysis.text_individual.text_analyze import run_text_pipeline
from src.analysis.text_individual.llm_summary import generate_text_llm_summary, generate_contribution_llm_summary, extract_key_role_llm
from src.analysis.code_collaborative.code_collaborative_analysis_helper import prompt_key_role
from src.analysis.text_individual.alt_summary import prompt_manual_summary
from src.analysis.skills.flows.text_skill_extraction import extract_text_skills
from src.utils.helpers import normalize_pdf_paragraphs
from src.db import get_files_with_timestamps, get_files_with_timestamps_for_version, get_latest_version_key, store_text_activity_contribution
from src.analysis.activity_type.text.activity_type import print_activity, get_activity_contribution_data
try:
    from src import constants
except ModuleNotFoundError:
    import constants
from src.analysis.text_collaborative.text_sections import extract_document_sections

def analyze_collaborative_text_project(
    conn,
    user_id,
    project_name,
    parsed_files,
    zip_path,
    external_consent,
    summary_obj,  # ProjectSummary instance
    version_key: int | None = None,
    main_file_relpath: str | None = None,
    contribution_inputs: dict | None = None,
    interactive: bool = True,
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
    contribution_inputs = contribution_inputs or {}
    manual_project_summary = str(contribution_inputs.get("manual_project_summary") or "").strip() or None

    # ---------------------------------------------------------
    # STEP 1 — Run main pipeline to get the full summary + skills
    # ---------------------------------------------------------
    pipeline_result = run_text_pipeline(
        parsed_files=parsed_files,
        zip_path=zip_path,
        conn=conn,
        user_id=user_id,
        project_name=project_name,
        version_key=version_key,
        consent=external_consent,
        suppress_print=True,
        main_file_relpath=main_file_relpath,
        interactive=interactive,
        manual_summary_override=manual_project_summary,
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
    
    # Combine with supporting text files for total word count
    full_project_text_parts = [full_main_text]

    all_supporting_text_files = [
        f for f in parsed_files
        if f["file_type"] == "text"
        and not f["file_name"].lower().endswith(".csv")
        and f["file_name"] != main_file_name
    ]

    for f in all_supporting_text_files:
        support_text = _load_main_text(parsed_files, f["file_name"], zip_path, conn, user_id)
        normalized_sup = normalize_pdf_paragraphs(support_text)
        clean_text = "\n\n".join(normalized_sup)
        full_project_text_parts.append(clean_text)

    full_project_text = "\n\n".join(full_project_text_parts)

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
    sections = extract_document_sections(full_main_text)
    if interactive:
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
                "percent_of_document": 0,
                "contribution_summary": "[No contributions provided]",
                "skills": {},
                "buckets": {},
                "overall_score": 0,
            }
            return
        indices = _parse_selected_indices(selected, len(sections))
    else:
        selected_ids = contribution_inputs.get("main_section_ids") or []
        indices = _valid_selected_indices(selected_ids, len(sections))

    user_sections = [sections[i - 1] for i in indices if 1 <= i <= len(sections)]

    # ---------------------------------------------------------
    # STEP 2A — Ask for contribution description (like code projects)
    # ---------------------------------------------------------
    if interactive:
        print("\nDescribe your personal contributions to this collaborative text project.")
        print("Write 1-3 sentences. Be specific about sections/content you primarily worked on.")
        try:
            contribution_desc = input(f"Your contribution to '{project_name}': ").strip()
        except EOFError:
            contribution_desc = ""
    else:
        contribution_desc = str(contribution_inputs.get("manual_contribution_summary") or "").strip()

    # Store the description
    summary_obj.contributions["manual_contribution_summary"] = contribution_desc or "[No manual contribution summary provided]"

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
        if interactive:
            print("\nWhich supporting TEXT files did you contribute to?")
            for idx, f in enumerate(supporting_text_files, start=1):
                print(f"  {idx}. {f['file_name']}")
            print("Enter numbers (comma-separated), or 0 for NONE.")

            resp = input("> ").strip()
            text_support_indices = _parse_selected_indices(resp, len(supporting_text_files), allow_zero=True)
            selected_text_support_files = [
                supporting_text_files[i - 1] for i in text_support_indices
            ]
        else:
            selected_text_support_files = _select_files_by_relpaths(
                supporting_text_files,
                contribution_inputs.get("supporting_text_relpaths") or [],
            )
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
        all_csv_metadata = pipeline_result.get("csv_metadata", {})
        files_metadata = all_csv_metadata.get("files", [])

        if interactive:
            print("\nWhich CSV files did you contribute to?")
            for idx, csv_f in enumerate(supporting_csv_files, start=1):
                print(f"  {idx}. {csv_f['file_name']}")
            print("Enter numbers (comma-separated), or 0 for NONE.")

            resp_csv = input("> ").strip()
            csv_support_indices = _parse_selected_indices(resp_csv, len(supporting_csv_files), allow_zero=True)
            selected_csv_files = [supporting_csv_files[i - 1] for i in csv_support_indices]
        else:
            selected_csv_files = _select_files_by_relpaths(
                supporting_csv_files,
                contribution_inputs.get("supporting_csv_relpaths") or [],
            )

        user_csv_metadata = _select_csv_metadata(files_metadata, selected_csv_files)
    else:
        print("\n(No CSV files detected.)")
        user_csv_metadata = None


    # ---------------------------------------------------------
    # MERGE ALL CONTRIBUTED TEXT
    # ---------------------------------------------------------
    contributed_text_parts = []
    if contributed_text.strip():
        contributed_text_parts.append(contributed_text.strip())
    contributed_text_parts.extend([txt.strip() for txt in contributed_supporting_texts if txt.strip()])
    contributed_text = "\n\n".join(contributed_text_parts)

    if not contributed_text and not (user_csv_metadata and user_csv_metadata.get("files")):
        print("[TEXT-COLLAB] No contributions selected; assuming 0 contribution.")
        summary_obj.contributions["text_collab"] = {
            "percent_of_document": 0,
            "contribution_summary": "[No contributions provided]",
            "skills": {},
            "buckets": {},
            "overall_score": 0,
        }
        preset_role = str(contribution_inputs.get("key_role") or "").strip()
        if preset_role:
            summary_obj.contributions["key_role"] = preset_role
        return

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

    # Fetch timestamp data for ALL project files (use version_key when available to avoid re-resolution)
    if version_key is not None:
        all_project_files = get_files_with_timestamps_for_version(conn, user_id, version_key)
    else:
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
        vk = version_key or get_latest_version_key(conn, user_id, project_name)
        if vk:
            store_text_activity_contribution(conn, vk, activity_data)

    # ---------------------------------------------------------
    # STEP 3 — Compute % of contribution
    # ---------------------------------------------------------
    user_wc = len(contributed_text.split())
    total_wc = len(full_project_text.split())
    pct = round((user_wc / total_wc) * 100, 2) if total_wc > 0 else 0

    # ---------------------------------------------------------
    # STEP 4 — FIRST-PERSON contribution summary
    # ---------------------------------------------------------
    if external_consent == "accepted":
        contribution_summary = generate_contribution_llm_summary(
            full_main_text, contributed_text
        )
    else:
        if interactive:
            contribution_summary = _manual_contribution_summary_prompt()
        else:
            contribution_summary = contribution_desc or "[No manual contribution summary provided]"

    if constants.VERBOSE:
        print("\n" + "="*80)
    print("YOUR CONTRIBUTION SUMMARY:")
    print(textwrap.fill(contribution_summary, width=80, subsequent_indent="  "))
    if constants.VERBOSE:
        print("="*80 + "\n")

    # ---------------------------------------------------------
    # STEP 4B — Extract or prompt for key role
    # ---------------------------------------------------------
    contribution_desc = summary_obj.contributions.get("manual_contribution_summary", "")
    preset_role = str(contribution_inputs.get("key_role") or "").strip()
    if preset_role:
        key_role = preset_role
    elif external_consent == "accepted" and contribution_desc and contribution_desc != "[No manual contribution summary provided]":
        key_role = extract_key_role_llm(contribution_desc)
    elif interactive:
        key_role = prompt_key_role(project_name)
    else:
        key_role = ""

    if key_role:
        summary_obj.contributions["key_role"] = key_role

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


def _normalize_relpath_like(value: str) -> str:
    return (value or "").replace("\\", "/").lstrip("./")


def _path_matches_target(file_path: str, file_name: str, target: str) -> bool:
    norm_file_path = _normalize_relpath_like(file_path)
    norm_file_name = _normalize_relpath_like(file_name)
    norm_target = _normalize_relpath_like(target)
    if not norm_target:
        return False

    if (
        norm_file_path == norm_target
        or norm_file_path.endswith("/" + norm_target)
        or norm_target.endswith("/" + norm_file_path)
    ):
        return True

    target_base = norm_target.rsplit("/", 1)[-1]
    return norm_file_name == target_base


def _select_files_by_relpaths(files: list[dict], relpaths: list[str]) -> list[dict]:
    targets = [_normalize_relpath_like(p) for p in (relpaths or []) if _normalize_relpath_like(p)]
    if not targets:
        return []

    selected: list[dict] = []
    seen: set[str] = set()
    for target in targets:
        for f in files:
            key = f.get("file_path") or f.get("file_name") or ""
            if _path_matches_target(f.get("file_path", ""), f.get("file_name", ""), target):
                if key not in seen:
                    seen.add(key)
                    selected.append(f)
                break
    return selected


def _select_csv_metadata(files_metadata: list[dict], selected_csv_files: list[dict]) -> dict | None:
    if not selected_csv_files:
        return None

    selected_relpaths = [
        _normalize_relpath_like(f.get("file_path", ""))
        for f in selected_csv_files
    ]
    selected_names = {
        (f.get("file_name") or "").strip()
        for f in selected_csv_files
        if (f.get("file_name") or "").strip()
    }

    chosen = []
    for meta in files_metadata or []:
        meta_path = _normalize_relpath_like(meta.get("file_path", ""))
        meta_name = (meta.get("file_name") or "").strip()
        matches_path = any(
            _path_matches_target(meta_path, meta_name, target)
            for target in selected_relpaths
            if target
        )
        if matches_path or (meta_name and meta_name in selected_names):
            chosen.append(meta)

    if not chosen:
        return None
    return {"files": chosen}


def _parse_selected_indices(raw: str, upper_bound: int, allow_zero: bool = False) -> list[int]:
    indices: list[int] = []
    if not raw:
        return indices

    for token in raw.split(","):
        token = token.strip()
        if not token.isdigit():
            print(f"[Warning] Ignoring invalid input: '{token}'")
            continue

        n = int(token)
        if allow_zero and n == 0:
            return []
        if 1 <= n <= upper_bound:
            indices.append(n)
        else:
            print(f"[Warning] Selection {n} is out of range.")

    return indices


def _valid_selected_indices(raw_values, upper_bound: int) -> list[int]:
    out: list[int] = []
    for val in raw_values or []:
        if isinstance(val, int) and 1 <= val <= upper_bound and val not in out:
            out.append(val)
    return out

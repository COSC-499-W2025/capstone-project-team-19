from __future__ import annotations
import sqlite3
from typing import Optional, Dict, Mapping, Any
import json
from datetime import datetime

from src.db import (
    store_github_account,
    store_collaboration_profile,
    store_file_contributions,
    insert_code_collaborative_metrics,
    get_metrics_id,
    insert_code_collaborative_summary
)
from src.integrations.github.github_oauth import github_oauth
from src.integrations.github.token_store import get_github_token
from src.integrations.github.link_repo import ensure_repo_link, select_and_store_repo, get_gh_repo_name_and_owner
from src.integrations.github.github_api import get_authenticated_user
from src.utils.framework_detector import detect_frameworks
from src.utils.language_detector import detect_languages
from src.utils.helpers import zip_paths  
from src.integrations.github.github_analysis import fetch_github_metrics
from src.integrations.github.db_repo_metrics import store_github_repo_metrics, get_github_repo_metrics, print_github_metrics_summary, store_github_detailed_metrics
from src.analysis.code_collaborative.github_collaboration.build_collab_metrics import run_collaboration_analysis
from src.analysis.code_collaborative.github_collaboration.print_collaboration_summary import print_collaboration_summary

from .code_collaborative_analysis_helper import (
    DEBUG,
    resolve_repo_for_project,
    ensure_user_github_table,
    load_user_github,
    save_user_github,
    collect_repo_authors,
    prompt_user_identity_choice,
    read_git_history,
    compute_metrics,
    print_project_card,
    print_portfolio_summary,
    prompt_collab_descriptions
)


_CODE_RUN_METRICS: list[dict] = []
_manual_descs_store: dict[str, str] = {}  # filled once per run for collab projects

def set_manual_descs_store(descs: dict[str, str] | None) -> None:
    """Store user-provided project descriptions for this analysis run."""
    global _manual_descs_store
    _manual_descs_store = descs or {}

def get_manual_desc(project_name: str) -> str:
    """Retrieve a stored description for a project if available."""
    if not _manual_descs_store:
        return ""
    return _manual_descs_store.get(project_name, "") or ""

def print_code_portfolio_summary() -> None:
    """
    Print a single combined portfolio summary for all code projects
    analyzed so far in this run, then clear the accumulator.
    Call this from project_analysis.py after your last code project.
    """
    if not _CODE_RUN_METRICS:
        return
    print_portfolio_summary(_CODE_RUN_METRICS)
    _CODE_RUN_METRICS.clear()

def analyze_code_project(conn: sqlite3.Connection,
                         user_id: int,
                         project_name: str,
                         zip_path: str,
                         summary=None) -> Optional[dict]:
    # 1) get base dirs from the uploaded zip
    zip_data_dir, zip_name, _ = zip_paths(zip_path)

    # 2) find repo (collaborative/ → DB classifications → files.file_path)
    repo_dir = resolve_repo_for_project(conn, zip_data_dir, zip_name, project_name, user_id)
    if not repo_dir:
        print(
            f"\nNo local Git repo found under allowed paths. "
            f"Zip a local clone (not GitHub 'Download ZIP') so .git is included."
        )

        _handle_no_git_repo(conn, user_id, project_name)
        _enhance_with_github(conn, user_id, project_name, repo_dir, summary)

        return None

    print(f"Found local Git repo for {project_name}")

    repo_metrics = _enhance_with_github(conn, user_id, project_name, repo_dir, summary)

    if DEBUG:
        print(f"[debug] repo resolved → {repo_dir}")

    # 3) identity table + load user aliases
    ensure_user_github_table(conn)
    aliases = load_user_github(conn, user_id)

    if not aliases["emails"] and not aliases["names"]:
        authors = collect_repo_authors(repo_dir)
        if not authors:
            print(f"\n[skip] {project_name}: no authors found in Git history.")
            return None
        sel_emails, sel_names = prompt_user_identity_choice(authors)
        if not sel_emails and not sel_names:
            print("\n[skip] No identities selected.")
            return None
        save_user_github(conn, user_id, sel_emails, sel_names)
        aliases = load_user_github(conn, user_id)

    # 4) read commits
    commits = read_git_history(repo_dir)
    if not commits:
        print(f"\n[skip] {project_name}: no commits detected.")
        return None

    # 5) compute metrics
    metrics = compute_metrics(project_name, repo_dir, commits, aliases)
    metrics["project_name"] = project_name

    # 5.1) attach manual description if it was collected up-front
    desc = get_manual_desc(project_name)

    if not desc:
        # Try to read external_consent; ignore errors if table/row doesn't exist.
        try:
            consent_row = conn.execute(
                "SELECT status FROM external_consent WHERE user_id = ?", (user_id,)
            ).fetchone()
            external_consent = consent_row[0] if consent_row else None
        except Exception:
            external_consent = None

        if external_consent != "accepted":
            try:
                user_desc = input(
                    f"Description for {project_name} (what the code does + your contribution): "
                )
            except EOFError:
                user_desc = ""
            desc = (user_desc or "").strip()
            
    if desc:
        metrics["desc"] = desc.strip()

    # 6) fill langs from DB if empty
    if not metrics.get("focus", {}).get("languages"):
        langs_from_db = detect_languages(conn, project_name) or []
        if langs_from_db:
            metrics["focus"]["languages"] = [f"{lang} (from DB)" for lang in langs_from_db]

    # 7) detect frameworks
    frameworks = detect_frameworks(conn, project_name, user_id, zip_path)
    if frameworks:
        metrics.setdefault("focus", {})["frameworks"] = sorted(frameworks)

    # 7.25) store languages and frameworks in summary
    if summary:
        focus = metrics.get("focus", {})
        languages = focus.get("languages", [])
        # Clean language names (remove "(from DB)" suffix if present)
        summary.languages = [lang.split(" (from DB)")[0] if " (from DB)" in lang else lang for lang in languages]
        summary.frameworks = focus.get("frameworks", [])
        # Store only the last commit date for skills timeline (minimal data)
        history = metrics.get("history", {})
        if history.get("last"):
            summary.metrics["collaborative_git"] = {
                "last_commit_date": history["last"]
            }
        # store non llm contribution summary    
        if desc and "llm_contribution_summary" not in summary.contributions:
            summary.contributions["non_llm_contribution_summary"] = desc.strip()

    # 7.5) save file contributions to database for skill extraction filtering
    file_contributions_data = metrics.get("file_contributions", {})
    if file_contributions_data:
        file_loc = file_contributions_data.get("file_loc", {})
        file_commits = file_contributions_data.get("file_commits", {})

        # Build the format expected by store_file_contributions
        contributions_dict = {}
        for file_path in file_loc.keys():
            contributions_dict[file_path] = {
                "lines_changed": file_loc.get(file_path, 0),
                "commits_count": file_commits.get(file_path, 0)
            }

        if contributions_dict:
            store_file_contributions(conn, user_id, project_name, contributions_dict)

    # 8) save aggregated git metrics into DB
    db_payload = _build_db_payload_from_metrics(metrics, repo_dir)
    insert_code_collaborative_metrics(conn, user_id, project_name, db_payload)
    metrics_id = get_metrics_id(conn, user_id, project_name)

    # 8.1) if we have a manual description, persist it as a non-LLM summary
    if metrics_id and desc:
        insert_code_collaborative_summary(
            conn,
            metrics_id=metrics_id,
            user_id=user_id,
            project_name=project_name,
            summary_type="non-llm",
            content=desc,
        )

    # 9) print
    print_project_card(metrics)
    # accumulate for portfolio summary
    _CODE_RUN_METRICS.append(metrics)

    return metrics


def _handle_no_git_repo(conn, user_id, project_name):
    token = get_github_token(conn, user_id)

    if token:
        print(f"\nNo local .git found for {project_name}, but a GitHub login already exists.")
        if ensure_repo_link(conn, user_id, project_name, token):
            print(f"[info] GitHub repo already linked for {project_name}")
            return None

        ans = input("Link this project to GitHub? (y/n): ").strip().lower()
        if ans in {"y", "yes"}:
            select_and_store_repo(conn, user_id, project_name, token)
        return None

    ans = input(
        f"No .git detected for {project_name}.\n"
        "Connect GitHub to analyze this project? (y/n): "
    ).strip().lower()

    if ans in {"y", "yes"}:
        token = github_oauth(conn, user_id)

        # get user's GitHub account info
        github_user = get_authenticated_user(token)
        store_github_account(conn, user_id, github_user)

        select_and_store_repo(conn, user_id, project_name, token)
        return None

    print(f"[skip] Skipping collaborative analysis for {project_name}")
    return None


def _enhance_with_github(conn, user_id, project_name, repo_dir, summary=None):
    ans = input("Enhance analysis with GitHub data? (y/n): ").strip().lower()
    if ans not in {"y", "yes"}:
        return
    
    try:
        token = get_github_token(conn, user_id)
        github_user = None

        if not token:
            token = github_oauth(conn, user_id)
            if not token:
                print("[GitHub] Auth cancelled or failed. Continuing without GitHub.")
                return

            github_user = get_authenticated_user(token)
            store_github_account(conn, user_id, github_user)
        else:
            github_user = get_authenticated_user(token)

        if not ensure_repo_link(conn, user_id, project_name, token):
            select_and_store_repo(conn, user_id, project_name, token)

        # get repo url
        owner, repo = get_gh_repo_name_and_owner(conn, user_id, project_name)
        if not owner: 
            print("[GitHub] No repo selected. Skipping GitHub metrics.")
            return # repo doesnt exist in db, nothing to analyze

        gh_username = github_user["login"]

        print("Collecting GitHub repository metrics...")

        # fetch metrics via github REST API then stoe metrics in db
        metrics = fetch_github_metrics(token, owner, repo, gh_username)
        collab_profile = run_collaboration_analysis(token, owner, repo, gh_username)

        if not metrics:
            print("[GitHub] Failed to fetch metrics. Skipping GitHub.")
            return

        store_github_repo_metrics(conn, user_id, project_name, owner, repo, metrics)
        store_github_detailed_metrics(conn, user_id, project_name, owner, repo, metrics)
        store_collaboration_profile(conn, user_id, project_name, owner, repo, collab_profile)

        repo_metrics = get_github_repo_metrics(conn, user_id, project_name, owner, repo)

        # If all metric sections are empty, skip
        if _metrics_empty(repo_metrics):
            print("No GitHub activity found for this repo.")
        else:
            print_collaboration_summary(collab_profile)

        if summary:
            summary.metrics["github"] = repo_metrics

        return repo_metrics

    except Exception as e:
        print(f"[GitHub] Error occurred ({e}). Skipping GitHub and continuing.")
        return None

# Determine if all metric categories show zero activity
def _metrics_empty(m: dict) -> bool:
    ignore = {"repository", "username"}
    for key, value in m.items():
        if key in ignore:
            continue

        if isinstance(value, dict):
            # if ANY nested field has meaningful value, activity exists
            if any(v not in (0, {}, [], None) for v in value.values()):
                return False
        else:
            if value not in (0, {}, [], None):
                return False

    return True

def _build_db_payload_from_metrics(metrics: Mapping[str, Any], repo_path: str) -> dict[str, Any]:
    """
    Flatten the compute_metrics() output into a dict that matches the
    code_collaborative_metrics table columns. This keeps db/ as pure CRUD.
    """
    totals = metrics.get("totals", {}) or {}
    loc = metrics.get("loc", {}) or {}
    history = metrics.get("history", {}) or {}
    focus = metrics.get("focus", {}) or {}

    def _to_iso(v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    first_commit = _to_iso(history.get("first"))
    last_commit = _to_iso(history.get("last"))

    languages = focus.get("languages") or []
    folders = focus.get("folders") or []
    top_files = focus.get("top_files") or []
    frameworks = focus.get("frameworks") or []

    return {
        "repo_path": repo_path,
        # totals
        "commits_all": totals.get("commits_all"),
        "commits_yours": totals.get("commits_yours"),
        "commits_coauth": totals.get("commits_coauth"),
        "merges": totals.get("merges"),
        # loc
        "loc_added": loc.get("added"),
        "loc_deleted": loc.get("deleted"),
        "loc_net": loc.get("net"),
        "files_touched": loc.get("files_touched"),
        "new_files": loc.get("new_files"),
        "renames": loc.get("renames"),
        # history
        "first_commit_at": first_commit,
        "last_commit_at": last_commit,
        "commits_L30": history.get("L30"),
        "commits_L90": history.get("L90"),
        "commits_L365": history.get("L365"),
        "longest_streak": history.get("longest_streak"),
        "current_streak": history.get("current_streak"),
        "top_days": history.get("top_days"),
        "top_hours": history.get("top_hours"),
        # focus (already JSON here)
        "languages_json": json.dumps(languages),
        "folders_json": json.dumps(folders),
        "top_files_json": json.dumps(top_files),
        "frameworks_json": json.dumps(frameworks),
    }

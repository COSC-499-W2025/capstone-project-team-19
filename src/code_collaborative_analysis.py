from __future__ import annotations
import sqlite3
from typing import Optional, Dict

from src.db import store_github_account
from src.github.github_oauth import github_oauth
from src.github.token_store import get_github_token
from src.github.link_repo import ensure_repo_link, select_and_store_repo, get_gh_repo_name_and_owner
from src.github.github_api import get_authenticated_user
from src.framework_detector import detect_frameworks
from src.language_detector import detect_languages
from src.helpers import zip_paths  
from src.github.github_analysis import fetch_github_metrics
from src.github.db_repo_metrics import store_github_repo_metrics, get_github_repo_metrics

from src.code_collaborative_analysis_helper import (
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
    print_github_metrics
)



_CODE_RUN_METRICS: list[dict] = []

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
                         zip_path: str) -> Optional[dict]:
    # 1) get base dirs from the uploaded zip
    zip_data_dir, zip_name, _ = zip_paths(zip_path)

    # 2) find repo (collaborative/ → DB classifications → files.file_path)
    repo_dir = resolve_repo_for_project(conn, zip_data_dir, zip_name, project_name, user_id)
    if not repo_dir:
        print(
            f"\nNo local Git repo found under allowed paths. "
            f"Zip a local clone (not GitHub 'Download ZIP') so .git is included."
        )
        return _handle_no_git_repo(conn, user_id, project_name)

    print(f"Found local Git repo for {project_name}")

    _enhance_with_github(conn, user_id, project_name, repo_dir)

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

    # 6) fill langs from DB if empty
    if not metrics.get("focus", {}).get("languages"):
        langs_from_db = detect_languages(conn, project_name) or []
        if langs_from_db:
            metrics["focus"]["languages"] = [f"{lang} (from DB)" for lang in langs_from_db]

    # 7) detect frameworks
    frameworks = detect_frameworks(conn, project_name, user_id, zip_path)
    if frameworks:
        metrics.setdefault("focus", {})["frameworks"] = sorted(frameworks)

    # 7.5) NEW — prompt for a one-line description (stored for printing/summary)
    try:
        user_desc = input(
            f"Description for {project_name} (what the code does + your contribution): "
        ).strip()
    except EOFError:
        user_desc = ""
    if user_desc:
        metrics["desc"] = user_desc

    # 8) print
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


def _enhance_with_github(conn, user_id, project_name, repo_dir):
    ans = input("Enhance analysis with GitHub data? (y/n): ").strip().lower()
    if ans not in {"y", "yes"}:
        return

    print("Collecting GitHub repository metrics...")
    
    token = get_github_token(conn, user_id)
    github_user = None

    if not token:
        token = github_oauth(conn, user_id)
        github_user = get_authenticated_user(token)
        store_github_account(conn, user_id, github_user)
    else:
        github_user = get_authenticated_user(token)

    if not ensure_repo_link(conn, user_id, project_name, token):
        select_and_store_repo(conn, user_id, project_name, token)

    # get repo url
    owner, repo = get_gh_repo_name_and_owner(conn, user_id, project_name)
    if not owner: return # repo doesnt exist in db, nothing to analyze

    gh_username = github_user["login"]

    # fetch metrics via github REST API then stoe metrics in db
    metrics = fetch_github_metrics(token, owner, repo, gh_username)
    store_github_repo_metrics(conn, user_id, project_name, owner, repo, metrics)
    
    repo_metrics = get_github_repo_metrics(conn, user_id, project_name, owner, repo)
    print("GitHub metrics collected. Analysis to be implemented.")
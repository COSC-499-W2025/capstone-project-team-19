"""
Collaborative CODE analyzer:
- Resolves repo location from the current upload
- Ensures user identity (one-time, saved to user_github)
- Extracts commit history via git
- Computes and prints per-project metrics
"""

from __future__ import annotations
import os
import datetime as dt
import subprocess
from collections import Counter
from typing import Dict, List, Optional, Tuple
from src.language_detector import detect_languages
from src.github_auth.github_oauth import github_oauth
from src.github_auth.token_store import get_github_token
from src.github_auth.link_repo import ensure_repo_link, select_and_store_repo

import sqlite3

# Local helpers
from src.helpers import zip_paths, is_git_repo, bfs_find_repo, ensure_table

DEBUG = False  # set True to troubleshoot path discovery

# -------------------------------------------------------------------------
# Public entry point (call from _analysis.py)
# -------------------------------------------------------------------------

def analyze_code_project(conn: sqlite3.Connection, user_id: int, project_name: str, zip_path: str) -> Optional[dict]:
    """
    Run collaborative code analysis for ONE project: resolve repo, select identity (once),
    read commits, compute YOUR metrics, print a card, return metrics dict (or None if skipped).
    """
    from src.language_detector import detect_languages  # import here to avoid top-level cross-import issues

    # 1) Resolve allowed base paths and find the repo root
    zip_data_dir, zip_name, _ = zip_paths(zip_path)
    repo_dir = _resolve_project_repo(zip_data_dir, zip_name, project_name)
    if not repo_dir:
        print(f"\nNo .git repo found in {project_name}.")

        token = get_github_token(conn, user_id)

        # no repo AND no GitHub token, skip automatically
        if not token:
            print(f"[skip] Skipping collaborative analysis for this project")
            return None

        print("GitHub already connected.")

        if ensure_repo_link(conn, user_id, project_name, token):
            return None
        
        ans = input("Connect GitHub to analyze this project? (y/n): ").strip().lower()
        if ans in {"y", "yes"}:
            select_and_store_repo(conn, user_id, project_name, token)

        return None
    
    # local repo exists - ask user if they want GitHub too
    print(f"Found local Git repo for {project_name}")
    token = get_github_token(conn, user_id)

    if token:
        try:
            ans = input("Enhance with GitHub data (stars, issues, PRs, repo metadata)? (y/n): ").strip().lower()
            if ans in {"y", "yes"}:
                if not ensure_repo_link(conn, user_id, project_name, token):
                    select_and_store_repo(conn, user_id, project_name, token)
        except Exception:
            # Test / non-interactive mode — do NOT block
            pass

    if DEBUG:
        print(f"[debug] repo resolved → {repo_dir}")

    # 2) Ensure identity table exists and load any saved identities
    _ensure_user_github_table(conn)
    aliases = _load_user_github(conn, user_id)

    # If nothing saved yet, scan this repo's authors and let user pick themselves once
    if not aliases["emails"] and not aliases["names"]:
        author_list = _collect_repo_authors(repo_dir)
        if not author_list:
            print(f"\n[skip] {project_name}: no authors found in Git history.")
            return None
        selected_emails, selected_names = _prompt_user_identity_choice(author_list)
        if not selected_emails and not selected_names:
            print("\n[skip] No identities selected.")
            return None
        _save_user_github(conn, user_id, selected_emails, selected_names)
        aliases = _load_user_github(conn, user_id)

    # 3) Read commits (with file numstats + name-status for renames)
    commits = _read_git_history(repo_dir)
    if not commits:
        print(f"\n[skip] {project_name}: no commits detected.")
        return None

    # 4) Compute metrics for YOUR contributions
    metrics = _compute_metrics(project_name, repo_dir, commits, aliases)

    # 5) If Git-based language focus is empty, fall back to DB-based detector
    if not metrics.get("focus", {}).get("languages"):
        langs_from_db = detect_languages(conn, project_name) or []
        if langs_from_db:
            metrics["focus"]["languages"] = [f"{lang} (from DB)" for lang in langs_from_db]

    # 6) Print the card and return metrics
    _print_project_card(metrics)
    return metrics


# -------------------------------------------------------------------------
# Repo resolution (two allowed bases + shallow nested scan)
# -------------------------------------------------------------------------

def _resolve_project_repo(zip_data_dir: str, zip_name: str, project_name: str) -> Optional[str]:
    """
    Try (in order):
      1) ./zip_data/<zip_name>/collaborative/<project>/
      2) ./zip_data/collaborative/<project>/
      3) Any ./zip_data/<zip_name>/**/collaborative/<project>/  (handles extra nesting like <zip_name>/<zip_name>/...)
    Then, for each candidate, if no .git at root, search up to 5 levels deeper for a nested repo.
    """
    # exact expected spots
    candidates = [
        os.path.join(zip_data_dir, zip_name, "collaborative", project_name),
        os.path.join(zip_data_dir, "collaborative", project_name),
    ]

    # NEW: scan under <zip_name> for any .../collaborative/<project>
    base_root = os.path.join(zip_data_dir, zip_name)
    if os.path.isdir(base_root):
        for root, dirs, files in os.walk(base_root):
            # stop overly deep crawls
            depth = os.path.relpath(root, base_root).count(os.sep)
            if depth > 5:
                continue
            if os.path.basename(root) == "collaborative":
                cand = os.path.join(root, project_name)
                if os.path.isdir(cand):
                    candidates.append(cand)

    # probe candidates
    for base in candidates:
        if DEBUG:
            print(f"[debug] probe base: {base}  (exists: {os.path.isdir(base)})")
        if not os.path.isdir(base):
            continue
        if is_git_repo(base):
            return base
        nested = bfs_find_repo(base, max_depth=5)  # was 2; allow deeper nesting
        if DEBUG:
            print(f"[debug] nested repo? {'YES → ' + nested if nested else 'no'}")
        if nested:
            return nested
    return None

# -------------------------------------------------------------------------
# DB: store/load user's GitHub commit identities (emails/names)
# -------------------------------------------------------------------------

def _ensure_user_github_table(conn: sqlite3.Connection) -> None:
    ensure_table(
        conn,
        "user_github",
        """
        CREATE TABLE IF NOT EXISTS user_github (
            user_id     INTEGER NOT NULL,
            email       TEXT,
            name        TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, email, name)
        )
        """
    )

def _load_user_github(conn: sqlite3.Connection, user_id: int) -> Dict[str, set]:
    emails, names = set(), set()
    cur = conn.execute("SELECT email, name FROM user_github WHERE user_id = ?", (user_id,))
    for em, nm in cur.fetchall():
        if em:
            emails.add(em.strip().lower())
        if nm:
            names.add(nm.strip().lower())
    return {"emails": emails, "names": names}

def _save_user_github(conn: sqlite3.Connection, user_id: int, emails: List[str], names: List[str]) -> None:
    cur = conn.cursor()
    for em in set(e.strip().lower() for e in emails if e.strip()):
        cur.execute("INSERT OR IGNORE INTO user_github(user_id, email, name) VALUES (?, ?, NULL)", (user_id, em))
    for nm in set(n.strip() for n in names if n.strip()):
        cur.execute("INSERT OR IGNORE INTO user_github(user_id, email, name) VALUES (?, NULL, ?)", (user_id, nm))
    conn.commit()
    print("\nSaved your identity for future runs")


# -------------------------------------------------------------------------
# Author discovery (for one-time selection)
# -------------------------------------------------------------------------

def _collect_repo_authors(repo_dir: str) -> List[Tuple[str, str, int]]:
    """
    Returns list of (author_name, author_email, count) within one repo.
    """
    out = _run_git(repo_dir, ["log", "--pretty=format:%an%x09%ae"])
    if not out:
        return []
    counts = Counter()
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            an = (parts[0] or "").strip()
            ae = (parts[1] or "").strip().lower()
            if an or ae:
                counts[(an, ae)] += 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0][0].lower(), kv[0][1]))
    return [(an, ae, c) for (an, ae), c in ranked]

def _prompt_user_identity_choice(author_list: List[Tuple[str, str, int]]) -> Tuple[List[str], List[str]]:
    print("\nWe found collaborators in this repo. Pick which identities are YOU.")
    print("Select multiple by numbers (e.g., 1,3,5) or press Enter to skip.\n")
    for i, (an, ae, c) in enumerate(author_list, start=1):
        label = f"{an} <{ae}>" if ae else an
        print(f"{i:3d}. {label}   [{c} commits]")

    choice = input("\nEnter numbers (comma-separated), or leave blank to skip: ").strip()
    if not choice:
        return [], []

    sel_idx = {int(tok) for tok in choice.replace(" ", "").split(",") if tok.isdigit()}
    emails, names = [], []
    for i in sorted(sel_idx):
        if 1 <= i <= len(author_list):
            an, ae, _ = author_list[i-1]
            if ae:
                emails.append(ae)
            if an:
                names.append(an)

    extra = input("Add any extra commit emails (comma-separated), or Enter to continue: ").strip()
    if extra:
        emails.extend([e.strip().lower() for e in extra.split(",") if e.strip()])
    return emails, names


# -------------------------------------------------------------------------
# Git log parsing (uses system `git`)
# -------------------------------------------------------------------------

def _run_git(repo_dir: str, args: List[str]) -> str:
    cmd = ["git", "-C", repo_dir] + args
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        msg = e.output.decode("utf-8", errors="replace")
        print(f"[git error] {' '.join(cmd)}\n{msg}")
        return ""

def _read_git_history(repo_dir: str) -> List[dict]:
    """
    Collect commit metadata + per-file numstat + name-status (to count renames).
    """
    fmt = r"%H%x09%an%x09%ae%x09%ad%x09%P%x09%s%x09%B"
    # metadata + numstat (no renames)
    log_numstat = _run_git(repo_dir, ["log", "--date=iso-strict", f"--pretty=format:{fmt}", "--numstat", "--no-renames"])
    # name-status (detect renames)
    log_namestatus = _run_git(repo_dir, ["log", "--date=iso-strict", "--name-status", f"--pretty=format:{fmt}"])
    return _parse_git_logs(log_numstat, log_namestatus)

def _parse_git_logs(log_numstat: str, log_namestatus: str) -> List[dict]:
    # Map commit_hash -> name-status rows
    name_status_map = {}
    cur_hash = None
    for line in log_namestatus.splitlines():
        if "\t" in line:
            parts = line.split("\t")
            if 2 <= len(parts) < 7:
                if cur_hash:
                    name_status_map.setdefault(cur_hash, []).append(parts)
                continue
        fields = line.split("\t")
        if len(fields) >= 7:
            cur_hash = fields[0]

    commits = []
    header = None
    pending_files: List[str] = []

    def looks_like_hash(s: str) -> bool:
        return len(s) >= 7 and all(c in "0123456789abcdef" for c in s[:7].lower())

    def flush(header_fields, files_rows):
        if not header_fields:
            return
        ch, an, ae, ad, parents, subj, body = header_fields[:7]
        parents_list = [p for p in parents.split() if p]
        is_merge = len(parents_list) > 1
        try:
            authored_at = dt.datetime.fromisoformat(ad.replace("Z", "+00:00"))
        except Exception:
            authored_at = None

        files = []
        for row in files_rows:
            parts = row.split("\t")
            if len(parts) == 3:
                add_s, del_s, path = parts
                if add_s == "-" or del_s == "-":
                    additions, deletions, is_binary = 0, 0, True
                else:
                    try:
                        additions = int(add_s)
                        deletions = int(del_s)
                    except ValueError:
                        additions, deletions = 0, 0
                    is_binary = False
                files.append({"path": path, "additions": additions, "deletions": deletions, "is_binary": is_binary})

        ns_counts = Counter()
        for row in name_status_map.get(ch, []):
            code = row[0]
            if code.startswith("R"):
                ns_counts["R"] += 1
            elif code in ("A", "M", "D"):
                ns_counts[code] += 1

        commits.append({
            "hash": ch,
            "author_name": an,
            "author_email": ae,
            "authored_at": authored_at,
            "parents": parents_list,
            "is_merge": is_merge,
            "subject": subj,
            "body": body or "",
            "files": files,
            "name_status": dict(ns_counts),
        })

    for line in log_numstat.splitlines():
        fields = line.split("\t")
        if len(fields) >= 7 and looks_like_hash(fields[0]):
            flush(header, pending_files)
            header = fields[:7]
            pending_files = []
        else:
            if not line.strip():
                continue
            pending_files.append(line)
    flush(header, pending_files)
    return commits


# -------------------------------------------------------------------------
# Identity matching + metrics
# -------------------------------------------------------------------------

def _is_authored_by_user(commit: dict, aliases: Dict[str, set]) -> bool:
    ae = (commit.get("author_email") or "").lower()
    an = (commit.get("author_name") or "").lower()
    if ae and ae in aliases["emails"]:
        return True
    if an:
        if an in aliases["names"]:
            return True
        for nm in aliases["names"]:
            if nm and nm in an:
                return True
    return False

def _is_coauthored_by_user(commit: dict, aliases: Dict[str, set]) -> bool:
    body = commit.get("body") or ""
    for ln in (ln.strip().lower() for ln in body.splitlines()):
        if ln.startswith("co-authored-by:"):
            lower = ln
            for em in aliases["emails"]:
                if em in lower:
                    return True
            for nm in aliases["names"]:
                if nm and nm in lower:
                    return True
    return False

def _compute_metrics(project: str, path: str, commits: List[dict], aliases: Dict[str, set]) -> dict:
    total_commits = len(commits)
    merges = sum(1 for c in commits if c["is_merge"])

    your_commits = [c for c in commits if _is_authored_by_user(c, aliases)]
    coauth_commits = [c for c in commits if _is_coauthored_by_user(c, aliases)]
    num_yours = len(your_commits)
    num_coauth = len(coauth_commits)

    add_sum = del_sum = file_touch = new_files = renames = 0
    lang_loc = Counter()
    folder_loc = Counter()
    file_loc = Counter()

    for c in your_commits:
        ns = c.get("name_status", {})
        new_files += ns.get("A", 0)
        renames  += ns.get("R", 0)

        for f in c["files"]:
            p = f["path"]
            additions = f["additions"]
            deletions = f["deletions"]
            add_sum += additions
            del_sum += deletions
            file_touch += 1

            loc = additions + deletions
            if loc > 0 and not f.get("is_binary", False):
                lang_loc[_ext(p)] += loc
                folder_loc[_top_folder(p)] += loc
                file_loc[p] += loc

    net = add_sum - del_sum

    first_dt = min((c["authored_at"] for c in commits if c["authored_at"]), default=None)
    last_dt  = max((c["authored_at"] for c in commits if c["authored_at"]), default=None)
    l30  = _count_in_last_days(your_commits, 30)
    l90  = _count_in_last_days(your_commits, 90)
    l365 = _count_in_last_days(your_commits, 365)
    longest_streak, current_streak = _streaks([c["authored_at"].date() for c in your_commits if c["authored_at"]])

    dow = Counter()
    hod = Counter()
    for c in your_commits:
        t = c.get("authored_at")
        if t:
            dow[t.strftime("%a")] += 1
            hod[t.hour] += 1
    top_days  = ", ".join([d for d, _ in dow.most_common(2)]) if dow else "—"
    top_hours = _top_hours(hod)

    langs_pct   = _top_share(lang_loc, label_from_ext=True)
    folders_pct = _top_share(folder_loc, limit=3)
    top_files   = [f for f, _ in file_loc.most_common(5)]

    return {
        "project": project,
        "path": path,
        "totals": {
            "commits_all": total_commits,
            "commits_yours": num_yours,
            "commits_coauth": num_coauth,
            "merges": merges,
        },
        "loc": {
            "added": add_sum,
            "deleted": del_sum,
            "net": net,
            "files_touched": file_touch,
            "new_files": new_files,
            "renames": renames,
        },
        "history": {
            "first": first_dt,
            "last": last_dt,
            "L30": l30,
            "L90": l90,
            "L365": l365,
            "longest_streak": longest_streak,
            "current_streak": current_streak,
            "top_days": top_days,
            "top_hours": top_hours,
        },
        "focus": {
            "languages": langs_pct,
            "folders": folders_pct,
            "top_files": top_files,
        }
    }

def _count_in_last_days(commits: List[dict], days: int) -> int:
    if not commits:
        return 0
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=days)
    return sum(1 for c in commits if c.get("authored_at") and c["authored_at"] >= cutoff)

def _streaks(dates: List[dt.date]) -> tuple[int, int]:
    if not dates:
        return 0, 0
    uniq = sorted(set(dates))
    longest = 1
    current = 1 if uniq and uniq[-1] == dt.date.today() else 0
    run = 1
    for i in range(1, len(uniq)):
        if (uniq[i] - uniq[i-1]).days == 1:
            run += 1
        else:
            longest = max(longest, run)
            run = 1
    longest = max(longest, run)
    return longest, current

def _top_hours(hod: Counter) -> str:
    if not hod:
        return "—"
    top = [h for h, _ in hod.most_common(3)]
    def fmt(h): return f"{h:02d}–{(h+1)%24:02d}h"
    return "  •  ".join(fmt(h) for h in top)

def _top_share(counter: Counter, label_from_ext=False, limit=5) -> List[str]:
    total = sum(counter.values())
    if total <= 0:
        return []
    items = counter.most_common(limit)
    out = []
    for k, v in items:
        pct = int(round(100 * v / total))
        label = _ext_to_lang(k) if label_from_ext else (k or "(root)")
        out.append(f"{label} {pct}%")
    return out

def _ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()

def _top_folder(path: str) -> str:
    parts = path.replace("\\", "/").split("/")
    return parts[0] if parts else ""

def _ext_to_lang(ext: str) -> str:
    m = {
        ".py": "Python", ".ipynb": "Jupyter", ".js": "JS", ".ts": "TS",
        ".tsx": "TSX", ".jsx": "JSX", ".java": "Java", ".cs": "C#",
        ".cpp": "C++", ".cxx": "C++", ".cc": "C++", ".c": "C",
        ".rs": "Rust", ".go": "Go", ".rb": "Ruby", ".php": "PHP",
        ".kt": "Kotlin", ".swift": "Swift", ".m": "Obj-C",
        ".h": "Header", ".hpp": "Header", ".hh": "Header",
        ".sql": "SQL", ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
        ".md": "Markdown", ".yml": "YAML", ".yaml": "YAML",
        ".sh": "Shell", ".ps1": "Powershell",
    }
    return m.get(ext, ext.replace(".", "").upper() or "Other")


# -------------------------------------------------------------------------
# CLI printing
# -------------------------------------------------------------------------
def _print_project_card(m: dict) -> None:
    h = m.get("history", {})
    t = m.get("totals", {})
    l = m.get("loc", {})
    f = m.get("focus", {})

    def dt_str(x):
        try:
            return x.astimezone().strftime("%Y-%m-%d") if x else "—"
        except Exception:
            return "—"

    langs     = ", ".join(f.get("languages", [])) or "—"
    folders   = ", ".join(f.get("folders", [])) or "—"
    top_files = ", ".join(f.get("top_files", [])) or "—"

    # Active days (inclusive)
    active_days = None
    if h.get("first") and h.get("last"):
        try:
            active_days = (h["last"].date() - h["first"].date()).days + 1
        except Exception:
            active_days = None

    # Extract top 1–2 language names (strip %)
    def _primary_langs():
        out = []
        for item in f.get("languages", [])[:2]:
            # item like "Python 72%" or "Python (from DB)"
            name = item.split()[0] if isinstance(item, str) and item else ""
            if name:
                out.append(name)
        return out

    prim = _primary_langs()

    # One-line summary for this project
    bits = [
        f"You made {t.get('commits_yours', 0)} of {t.get('commits_all', 0)} commits",
        f"({l.get('net', 0):+,.0f} net lines)"
    ]
    if prim:
        bits.append("mainly in " + " and ".join(prim[:2]))
    if active_days and active_days > 0:
        bits.append(f"over {active_days} day{'s' if active_days != 1 else ''}")
    summary_line = "💡 Summary: " + ", ".join(bits) + "."

    print(f"""
Project: {m.get('project','—')}
------------------------------------
Commits: {t.get('commits_all',0)} (You: {t.get('commits_yours',0)} | Co-authored: {t.get('commits_coauth',0)} | Merges: {t.get('merges',0)})
Lines: +{l.get('added',0):,} / -{l.get('deleted',0):,}  →  Net {('+' if l.get('net',0)>=0 else '')}{l.get('net',0):,}
Files: changed {l.get('files_touched',0)}  |  new {l.get('new_files',0)}  |  renames {l.get('renames',0)}

Active: {dt_str(h.get('first'))} → {dt_str(h.get('last'))}   |   L30: {h.get('L30',0)}  L90: {h.get('L90',0)}  L365: {h.get('L365',0)}
Streaks: longest {h.get('longest_streak',0)} days   |   current {h.get('current_streak',0)} days
Focus: {langs}
Top folders: {folders}
Top files: {top_files}
{summary_line}
""".rstrip())
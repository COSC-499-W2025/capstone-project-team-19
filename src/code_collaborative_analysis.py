# git_contrib.py
import datetime as dt
import sqlite3
import os
from collections import Counter
from typing import Dict, List, Optional, Tuple

from helpers import (
    resolve_zip_base,
    find_project_dir,
    is_git_repo,
    run_git,
    file_ext,
    top_folder,
    ext_to_lang,
)
from language_detector import detect_languages  # DB-declared languages

from helpers import _fetch_files
from parsing import ZIP_DATA_DIR  

def analyze_project_commits(conn, user_id, project_name, zip_path=None):
    """
    Analyze Git commits for a collaborative project.
    - First, try to locate the project folder via DB (_fetch_files)
    - Fallback: try zip_path if needed
    """

    project_dir = _resolve_project_dir_from_db(conn, user_id, project_name)
    if not project_dir:
        return None
    
    # 1️) Try to infer the project folder from DB entries
    files = _fetch_files(conn, user_id, project_name)
    project_dir = None

    if files:
        # get a common prefix path for all files in the project
        paths = [f["file_path"] for f in files if f["file_path"]]
        if paths:
            # the directory up to project folder
            common = os.path.commonpath(paths)
            # walk up until you reach the project name directory
            while common and os.path.basename(common) != project_name:
                parent = os.path.dirname(common)
                if parent == common:
                    break
                common = parent
            if os.path.basename(common) == project_name:
                project_dir = common

    # 2️) Fallback: try to find project folder relative to zip_path if DB paths fail
    if not project_dir and zip_path:
        zip_base = os.path.splitext(os.path.basename(zip_path))[0]
        guess_path = os.path.join("zip_data", zip_base)
        for root, dirs, _ in os.walk(guess_path):
            if os.path.basename(root) == project_name:
                project_dir = root
                break

    if not project_dir or not os.path.isdir(project_dir):
        print(f"[WARN] Could not locate folder for project '{project_name}'")
        return None

    # 3) Ensure there's a .git folder
    if not os.path.isdir(os.path.join(project_dir, ".git")):
        print(f"[WARN] Found folder but no .git at: {project_dir}")
        return None


    print(f"[git] Found project folder: {project_dir}")

    # 4️4) Run Git commands (e.g., count commits per author)
    import subprocess
    try:
        result = subprocess.run(
            ["git", "-C", project_dir, "shortlog", "-sne"],
            capture_output=True,
            text=True,
            check=True
        )
        return parse_git_shortlog(result.stdout, project_name)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] git analysis failed for {project_name}: {e}")
        return None

def print_project_card(m: dict) -> None:
    _print_project_card(m)


# =========================
# Identity aliases (DB)
# =========================

def ensure_alias_table(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_aliases (
            user_id     INTEGER NOT NULL,
            email       TEXT,
            name        TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, email, name)
        )
    """)
    conn.commit()


def load_aliases_for_user(conn: sqlite3.Connection, user_id: int) -> Dict[str, set]:
    emails, names = set(), set()
    cur = conn.cursor()
    cur.execute("SELECT email, name FROM user_aliases WHERE user_id = ?", (user_id,))
    for email, name in cur.fetchall():
        if email:
            emails.add(email.lower())
        if name:
            names.add(name.lower())
    return {"emails": emails, "names": names}


def save_aliases_for_user(conn: sqlite3.Connection, user_id: int, emails: List[str], names: List[str]) -> None:
    cur = conn.cursor()
    for em in set(e.strip().lower() for e in emails if e):
        cur.execute("INSERT OR IGNORE INTO user_aliases(user_id, email, name) VALUES (?, ?, NULL)", (user_id, em))
    for nm in set(n.strip() for n in names if n):
        cur.execute("INSERT OR IGNORE INTO user_aliases(user_id, email, name) VALUES (?, NULL, ?)", (user_id, nm))
    conn.commit()
    print("Saved your identity for future runs ✅")


def collect_authors(repo_dir: str) -> List[Tuple[str, str, int]]:
    out = run_git(repo_dir, ["log", "--pretty=format:%an%x09%ae"])
    counts = Counter()
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            an = (parts[0] or "").strip()
            ae = (parts[1] or "").strip().lower()
            if ae or an:
                counts[(an, ae)] += 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0][0].lower(), kv[0][1]))
    return [(an, ae, c) for (an, ae), c in ranked]


def prompt_user_identity_choice(author_list: List[Tuple[str, str, int]]) -> Tuple[List[str], List[str]]:
    print("\nWe found collaborators. Pick which identities are YOU (e.g., 1,3,5). Enter to skip.")
    for i, (an, ae, c) in enumerate(author_list, start=1):
        label = f"{an} <{ae}>" if ae else an
        print(f"{i:3d}. {label}   [{c} commits]")
    choice = input("\nEnter numbers (comma-separated), or leave blank to skip: ").strip()
    if not choice:
        return [], []
    sel_idx = {int(tok.strip()) for tok in choice.split(",") if tok.strip().isdigit()}
    emails, names = [], []
    for i in sorted(sel_idx):
        if 1 <= i <= len(author_list):
            an, ae, _ = author_list[i-1]
            if ae:
                emails.append(ae)
            if an:
                names.append(an)
    extra = input("Add extra commit emails (comma-separated), or Enter to continue: ").strip()
    if extra:
        emails.extend([e.strip().lower() for e in extra.split(",") if e.strip()])
    return sorted(set(emails)), sorted(set(names))


# =========================
# Git reading & parsing
# =========================

def read_git_history(repo_dir: str) -> List[dict]:
    """
    Read commit metadata + numstat + name-status (to detect renames/adds/deletes).
    """
    fmt = r"%H%x09%an%x09%ae%x09%ad%x09%P%x09%s%x09%B"
    log_numstat = run_git(
        repo_dir, ["log", "--date=iso-strict", f"--pretty=format:{fmt}", "--numstat", "--no-renames"]
    )
    log_namestatus = run_git(
        repo_dir, ["log", "--date=iso-strict", "--name-status", f"--pretty=format:{fmt}"]
    )
    return _parse_git_logs(log_numstat, log_namestatus)


def parse_git_shortlog(output, project_name):
    """Parse `git shortlog -sne` output into structured metrics."""
    metrics = []
    for line in output.strip().splitlines():
        parts = line.strip().split("\t")
        if len(parts) == 2:
            commits, author = parts
            metrics.append({"project": project_name, "author": author, "commits": int(commits)})
    return metrics

def _parse_git_logs(log_numstat: str, log_namestatus: str) -> List[dict]:
    # Map commit_hash -> name-status rows
    name_status_map: Dict[str, List[List[str]]] = {}
    current_hash: Optional[str] = None

    for line in log_namestatus.splitlines():
        if "\t" in line:
            parts = line.split("\t")
            if 2 <= len(parts) < 7:
                if current_hash:
                    name_status_map.setdefault(current_hash, []).append(parts)
                continue
        fields = line.split("\t")
        if len(fields) >= 7:
            current_hash = fields[0]

    commits: List[dict] = []
    header: Optional[List[str]] = None
    pending_files: List[str] = []

    def looks_like_hash(s: str) -> bool:
        return len(s) >= 7 and all(c in "0123456789abcdef" for c in s[:7].lower())

    def flush_commit(header_fields: Optional[List[str]], files_rows: List[str]) -> None:
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
                        additions = deletions = 0
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
            flush_commit(header, pending_files)
            header = fields[:7]
            pending_files = []
        else:
            if line.strip():
                pending_files.append(line)

    flush_commit(header, pending_files)
    return commits


# =========================
# Metrics
# =========================

def compute_metrics(project: str, path: str, commits: List[dict], aliases: Dict[str, set]) -> dict:
    total_commits = len(commits)
    merges = sum(1 for c in commits if c["is_merge"])

    your_commits = [c for c in commits if _is_authored_by_user(c, aliases)]
    coauth_commits = [c for c in commits if _is_coauthored_by_user(c, aliases)]
    num_yours = len(your_commits)
    num_coauth = len(coauth_commits)

    add_sum = del_sum = file_touch = new_files = renames = 0
    lang_loc: Counter = Counter()
    folder_loc: Counter = Counter()
    file_loc: Counter = Counter()

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
                lang_loc[file_ext(p)] += loc
                folder_loc[top_folder(p)] += loc
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
            "languages": langs_pct,   # from Git churn by extension
            "folders": folders_pct,
            "top_files": top_files,
        }
    }


def _lang_labels_from_git(metrics: dict) -> List[str]:
    """Turn focus.languages list (e.g., 'Python 68%') into bare language labels."""
    out = []
    for item in metrics.get("focus", {}).get("languages", []):
        parts = item.rsplit(" ", 1)
        out.append(parts[0] if parts else item)
    return out


# =========================
# Small helpers
# =========================

def _is_authored_by_user(commit: dict, aliases: Dict[str, set]) -> bool:
    ae = (commit.get("author_email") or "").lower()
    an = (commit.get("author_name") or "").lower()
    if ae and ae in aliases["emails"]:
        return True
    if an:
        if an in aliases["names"]:
            return True
        for n in aliases["names"]:
            if n and n in an:
                return True
    return False


def _is_coauthored_by_user(commit: dict, aliases: Dict[str, set]) -> bool:
    body = (commit.get("body") or "").lower()
    for ln in (ln.strip() for ln in body.splitlines()):
        if ln.startswith("co-authored-by:"):
            if any(em in ln for em in aliases["emails"]):
                return True
            if any(n and n in ln for n in aliases["names"]):
                return True
    return False


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
        label = ext_to_lang(k) if label_from_ext else (k or "(root)")
        out.append(f"{label} {pct}%")
    return out


def _print_project_card(m: dict) -> None:
    h = m["history"]; t = m["totals"]; l = m["loc"]; f = m["focus"]
    def dt_str(x):
        if not x:
            return "—"
        return x.astimezone().strftime("%Y-%m-%d")
    langs = ", ".join(f["languages"]) if f["languages"] else "—"
    folders = ", ".join(f["folders"]) if f["folders"] else "—"
    top_files = ", ".join(f["top_files"]) if f["top_files"] else "—"

    lang_section = ""
    if "languages" in m:
        dec = m["languages"].get("declared_in_db", [])
        obs = m["languages"].get("observed_in_git", [])
        ovl = m["languages"].get("overlap", [])
        lang_section = (
            f"\nLanguages (DB vs Git): DB={', '.join(dec) or '—'} | Git={', '.join(obs) or '—'}"
            + (f" | Overlap={', '.join(ovl) or '—'}" if dec or obs else "")
        )

    print(f"""
Project: {m['project']}
Path: {m['path']}
------------------------------------
Commits: {t['commits_all']} (You: {t['commits_yours']} | Co-authored: {t['commits_coauth']} | Merges: {t['merges']})
Lines: +{l['added']:,} / -{l['deleted']:,}  →  Net {('+' if l['net']>=0 else '')}{l['net']:,}
Files: changed {l['files_touched']}  |  new {l['new_files']}  |  renames {l['renames']}

Active: {dt_str(h['first'])} → {dt_str(h['last'])}   |   L30: {h['L30']}  L90: {h['L90']}  L365: {h['L365']}
Streaks: longest {h['longest_streak']} days   |   current {h['current_streak']} days
Focus (Git churn): {langs}
Top folders: {folders}
Top files: {top_files}{lang_section}
""".rstrip())

# additional
import os
import sqlite3
from typing import Optional, List, Dict

from parsing import ZIP_DATA_DIR
from helpers import _fetch_files

def _get_zip_name_for_project(conn: sqlite3.Connection, user_id: int, project_name: str) -> Optional[str]:
    row = conn.execute(
        """
        SELECT zip_name
        FROM project_classifications
        WHERE user_id = ? AND project_name = ?
        ORDER BY rowid DESC
        LIMIT 1
        """,
        (user_id, project_name),
    ).fetchone()
    return row[0] if row else None


def _resolve_project_dir_from_db(conn: sqlite3.Connection, user_id: int, project_name: str) -> Optional[str]:
    """
    Build absolute path = ZIP_DATA_DIR / zip_name / file_path_from_db, then
    walk upward from there until a directory containing '.git' is found.
    Prefer a repo whose basename == project_name, but accept any '.git' root.
    """
    zip_name = _get_zip_name_for_project(conn, user_id, project_name)
    if not zip_name:
        print(f"[WARN] zip_name not found for '{project_name}'")
        return None

    files: List[Dict[str, str]] = _fetch_files(conn, user_id, project_name)
    if not files:
        print(f"[WARN] No files for '{project_name}' in files table")
        return None

    base = os.path.join(ZIP_DATA_DIR, zip_name)
    samples = [f["file_path"] for f in files if f.get("file_path")]
    samples = samples[:20] if len(samples) > 20 else samples

    print(f"[DEBUG] ZIP_DATA_DIR={ZIP_DATA_DIR}")
    print(f"[DEBUG] zip_name={zip_name}")
    if samples:
        print(f"[DEBUG] sample file_path[0]={samples[0]}")

    any_git_root = None

    for rel in samples:
        abs_path = os.path.normpath(os.path.join(base, rel))
        cur = abs_path if os.path.isdir(abs_path) else os.path.dirname(abs_path)

        if not os.path.exists(cur):
            print(f"[DEBUG] path does not exist: {cur}")
            continue

        # climb up until filesystem root
        while True:
            git_dir = os.path.join(cur, ".git")
            if os.path.isdir(git_dir):
                # Found a repo root. Prefer a match to project_name; else keep first seen.
                if os.path.basename(cur) == project_name:
                    print(f"[DEBUG] repo root (exact match): {cur}")
                    return cur
                if any_git_root is None:
                    any_git_root = cur  # remember first repo root we encounter
                break  # stop climbing for this sample; try next sample

            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent

    if any_git_root:
        print(f"[WARN] Repo root found but folder name != '{project_name}': {any_git_root}")
        return any_git_root

    # Last resort: scan inside this upload only
    search_root = base
    for root, dirs, _ in os.walk(search_root):
        # modest depth limit
        if root.count(os.sep) - search_root.count(os.sep) > 7:
            dirs[:] = []
            continue
        if os.path.isdir(os.path.join(root, ".git")):
            # Prefer matching project_name if possible
            if os.path.basename(root) == project_name:
                print(f"[DEBUG] fallback repo root (exact): {root}")
                return root
            if any_git_root is None:
                any_git_root = root

    if any_git_root:
        print(f"[WARN] Fallback repo root found but folder name != '{project_name}': {any_git_root}")
        return any_git_root

    print(f"[WARN] Could not locate a Git repo for project '{project_name}' under {search_root}")
    return None

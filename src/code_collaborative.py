# code_collaborative.py
import os
import subprocess
import datetime as dt
from collections import Counter
from typing import Dict, List, Optional, Tuple

# ======================================================================================
# Public entry point
# ======================================================================================

def analyze_collaborative_projects(conn, user_id: int, zip_path: str, username: Optional[str] = None) -> None:
    """
    End-to-end: find collaborative projects for this upload, locate folders, detect .git,
    read commits, compute metrics, and print per-project + global summary.
    If username is not provided, politely ask for the GitHub username or commit email.
    """
    # Ask for identity if not provided
    if not username:
        username = input("Enter your GitHub username OR the email used in your commits (for authorship matching): ").strip()

    base_path, zip_name = _resolve_zip_base(zip_path)
    projects = _get_collaborative_projects(conn, user_id, zip_name)
    if not projects:
        print("\nNo collaborative projects found for this upload.")
        return

    aliases = _load_aliases(username)

    all_project_metrics = []
    for proj in projects:
        proj_dir = _find_project_dir(base_path, proj)
        if not proj_dir:
            print(f"\n[skip] Project '{proj}': folder not found under {base_path}")
            continue
        if not _is_git_repo(proj_dir):
            print(f"\n[skip] Project '{proj}': .git not found at {proj_dir}")
            continue

        commits = _read_git_history(proj_dir)
        if not commits:
            print(f"\n[skip] Project '{proj}': no commits detected")
            continue

        metrics = _compute_metrics(proj, proj_dir, commits, aliases)
        _print_project_card(metrics)
        all_project_metrics.append(metrics)

    if all_project_metrics:
        _print_global_summary(all_project_metrics)
    else:
        print("\nNo project produced metrics to summarize.")

# ======================================================================================
# Resolve base path
# ======================================================================================

def _resolve_zip_base(zip_path: str) -> Tuple[str, str]:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_data_dir = os.path.join(repo_root, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(zip_data_dir, zip_name)
    return base_path, zip_name

# ======================================================================================
# DB: get collaborative projects for this user + upload
# ======================================================================================

def _get_collaborative_projects(conn, user_id: int, zip_name: str) -> List[str]:
    """
    Reads project names from project_classifications where classification='collaborative'.
    """
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT project_name
            FROM project_classifications
            WHERE user_id = ? AND zip_name = ? AND classification = 'collaborative'
        """, (user_id, zip_name))
        rows = cur.fetchall()
        return [r[0] for r in rows]
    except Exception as e:
        print(f"[warn] Could not read project_classifications: {e}")
        return []

# ======================================================================================
# Locate project directory
# ======================================================================================

def _find_project_dir(base_path: str, project_name: str) -> Optional[str]:
    """
    Try:
      - <base>/<project_name>/
      - <base>/collaborative/<project_name>/
    """
    candidates = [
        os.path.join(base_path, project_name),
        os.path.join(base_path, "collaborative", project_name),
    ]
    for p in candidates:
        if os.path.isdir(p):
            return p
    return None

# ======================================================================================
# Git helpers (uses system `git`)
# ======================================================================================

def _is_git_repo(repo_dir: str) -> bool:
    git_dir = os.path.join(repo_dir, ".git")
    if os.path.isdir(git_dir):
        return True
    if os.path.isfile(git_dir):
        # worktrees: .git is a file pointing to a gitdir
        try:
            with open(git_dir, "r", encoding="utf-8", errors="ignore") as f:
                return "gitdir:" in f.read().lower()
        except Exception:
            return False
    return False

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
    Read commit metadata + numstat + name-status for rename/add/delete counts.
    """
    fmt = r"%H%x09%an%x09%ae%x09%ad%x09%P%x09%s%x09%B"

    # 1) metadata + numstat (no renames)
    log_numstat = _run_git(
        repo_dir,
        ["log", "--date=iso-strict", f"--pretty=format:{fmt}", "--numstat", "--no-renames"]
    )

    # 2) name-status to detect renames
    log_namestatus = _run_git(
        repo_dir,
        ["log", "--date=iso-strict", "--name-status", f"--pretty=format:{fmt}"]
    )

    return _parse_git_logs(log_numstat, log_namestatus)

def _parse_git_logs(log_numstat: str, log_namestatus: str) -> List[dict]:
    # Map commit_hash -> name-status rows
    name_status_map = {}
    current_hash = None
    for line in log_namestatus.splitlines():
        if "\t" in line:
            parts = line.split("\t")
            # name-status rows usually 2+ cols, commit header has 7 from fmt
            if 2 <= len(parts) < 7:
                if current_hash:
                    name_status_map.setdefault(current_hash, []).append(parts)
                continue
        fields = line.split("\t")
        if len(fields) >= 7:
            current_hash = fields[0]

    commits = []
    header = None
    pending_files = []

    def flush_commit(header_fields, files_rows):
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
        if len(fields) >= 7 and _looks_like_hash(fields[0]):
            # new header
            flush_commit(header, pending_files)
            header = fields[:7]
            pending_files = []
        else:
            if not line.strip():
                continue
            pending_files.append(line)

    flush_commit(header, pending_files)
    return commits

def _looks_like_hash(s: str) -> bool:
    return len(s) >= 7 and all(c in "0123456789abcdef" for c in s[:7].lower())

# ======================================================================================
# Identity / aliases
# ======================================================================================

def _load_aliases(username_or_email: Optional[str]) -> Dict[str, set]:
    """
    Build a minimal alias set from:
      - provided username_or_email (if contains '@' → email; else → name fragment)
      - optional config/aliases.yaml (emails/names lists)
      - optional env var WORKSTATS_ALIASES="email1;email2;name:Exact Name"
    """
    emails, names = set(), set()

    # from input
    if username_or_email:
        if "@" in username_or_email:
            emails.add(username_or_email.lower())
        else:
            names.add(username_or_email.strip().lower())

    # YAML (optional)
    here = os.path.dirname(os.path.abspath(__file__))
    cfg = os.path.join(os.path.dirname(here), "config", "aliases.yaml")
    if os.path.isfile(cfg):
        try:
            import re
            with open(cfg, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            # very light-weight parse: comma-separated lists inside []
            def _grab_list(key: str):
                m = re.search(rf"{key}\s*:\s*\[(.*?)\]", text, flags=re.S | re.I)
                if not m:
                    return []
                raw = m.group(1)
                return [x.strip().strip("'\"").lower() for x in raw.split(",") if x.strip()]
            emails.update(_grab_list("emails"))
            names.update(_grab_list("names"))
        except Exception:
            pass

    # ENV
    env = os.getenv("WORKSTATS_ALIASES", "")
    if env:
        for tok in env.split(";"):
            tok = tok.strip()
            if not tok:
                continue
            if tok.startswith("name:"):
                names.add(tok[5:].strip().lower())
            elif "@" in tok:
                emails.add(tok.lower())

    return {"emails": emails, "names": names}

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
    body = commit.get("body") or ""
    lines = [ln.strip() for ln in body.splitlines()]
    for ln in lines:
        if ln.lower().startswith("co-authored-by:"):
            lower = ln.lower()
            for em in aliases["emails"]:
                if em in lower:
                    return True
            for nm in aliases["names"]:
                if nm and nm in lower:
                    return True
    return False

# ======================================================================================
# Metrics
# ======================================================================================

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

    # Dates & activity
    first_dt = min((c["authored_at"] for c in commits if c["authored_at"]), default=None)
    last_dt  = max((c["authored_at"] for c in commits if c["authored_at"]), default=None)
    l30  = _count_in_last_days(your_commits, 30)
    l90  = _count_in_last_days(your_commits, 90)
    l365 = _count_in_last_days(your_commits, 365)
    longest_streak, current_streak = _streaks([c["authored_at"].date() for c in your_commits if c["authored_at"]])

    # When you code
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

# ======================================================================================
# CLI printing
# ======================================================================================

def _print_project_card(m: dict) -> None:
    h = m["history"]
    t = m["totals"]
    l = m["loc"]
    f = m["focus"]

    def dt_str(x):
        if not x:
            return "—"
        return x.astimezone().strftime("%Y-%m-%d")

    langs = ", ".join(f["languages"]) if f["languages"] else "—"
    folders = ", ".join(f["folders"]) if f["folders"] else "—"
    top_files = ", ".join(f["top_files"]) if f["top_files"] else "—"

    print(f"""
Project: {m['project']}
Path: {m['path']}
------------------------------------
Commits: {t['commits_all']} (You: {t['commits_yours']} | Co-authored: {t['commits_coauth']} | Merges: {t['merges']})
Lines: +{l['added']:,} / -{l['deleted']:,}  →  Net {('+' if l['net']>=0 else '')}{l['net']:,}
Files: changed {l['files_touched']}  |  new {l['new_files']}  |  renames {l['renames']}

Active: {dt_str(h['first'])} → {dt_str(h['last'])}   |   L30: {h['L30']}  L90: {h['L90']}  L365: {h['L365']}
Streaks: longest {h['longest_streak']} days   |   current {h['current_streak']} days
Focus: {langs}
Top folders: {folders}
Top files: {top_files}
""".rstrip())

def _print_global_summary(all_metrics: List[dict]) -> None:
    projects = len(all_metrics)
    your_commits = sum(m["totals"]["commits_yours"] for m in all_metrics)
    added = sum(m["loc"]["added"] for m in all_metrics)
    deleted = sum(m["loc"]["deleted"] for m in all_metrics)
    net = added - deleted

    most_active = max(all_metrics, key=lambda m: m["totals"]["commits_yours"]) if all_metrics else None

    lang_totals = Counter()
    for m in all_metrics:
        for item in m["focus"]["languages"]:
            parts = item.split()
            if parts:
                lang_totals[parts[0]] += 1
    top_lang = lang_totals.most_common(1)[0][0] if lang_totals else "—"

    print(f"""
Summary (collaborative projects in this upload)
------------------------------------
Projects: {projects}
Your commits: {your_commits}
Lines changed: +{added:,} / -{deleted:,}  →  Net {('+' if net>=0 else '')}{net:,}
Most active project: {most_active['project']} ({most_active['totals']['commits_yours']} your commits)""" + (f"""
Most used language: {top_lang}""" if top_lang != "—" else "") + "\n")

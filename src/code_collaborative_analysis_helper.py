from __future__ import annotations
import os
import datetime as dt
import subprocess
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple
import sqlite3

from src.extension_catalog import get_languages_for_extension
from src.helpers import ensure_table 
# zip_paths stays in the main file because only the entrypoint needs it

import re

DEBUG = False


# ------------------------------------------------------------
# 1. Repo resolution (3 tiers)
# ------------------------------------------------------------
def resolve_repo_for_project(conn: sqlite3.Connection,
                             zip_data_dir: str,
                             zip_name: str,
                             project_name: str,
                             user_id: int | str) -> Optional[str]:
    # 1) ./zip_data/.../collaborative/<project>
    repo = _resolve_from_collaborative_folder(zip_data_dir, zip_name, project_name)
    if repo:
        return repo

    # 2) project_classifications (collaborative+code)
    repo = _resolve_from_db_classification(conn, zip_data_dir, zip_name, project_name, user_id)
    if repo:
        return repo

    # 3) files.file_path guessing
    repo = _resolve_from_files_table(conn, zip_data_dir, project_name)
    return repo


def _resolve_from_collaborative_folder(zip_data_dir: str,
                                       zip_name: str,
                                       project_name: str) -> Optional[str]:
    candidates = [
        os.path.join(zip_data_dir, zip_name, "collaborative", project_name),
        os.path.join(zip_data_dir, "collaborative", project_name),
    ]

    base_root = os.path.join(zip_data_dir, zip_name)
    if os.path.isdir(base_root):
        for root, dirs, files in os.walk(base_root):
            depth = os.path.relpath(root, base_root).count(os.sep)
            if depth > 5:
                continue
            if os.path.basename(root) == "collaborative":
                cand = os.path.join(root, project_name)
                if os.path.isdir(cand):
                    candidates.append(cand)

    for base in candidates:
        if not os.path.isdir(base):
            continue
        if is_git_repo(base):
            return base
        nested = bfs_find_repo(base, max_depth=5)
        if nested:
            return nested
    return None


def _resolve_from_db_classification(conn: sqlite3.Connection,
                                    zip_data_dir: str,
                                    zip_name: str,
                                    wanted: str,
                                    user_id: int | str) -> Optional[str]:
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT project_name
            FROM project_classifications
            WHERE classification = 'collaborative'
              AND project_type   = 'code'
              AND user_id        = ?
              AND zip_name       = ?
            """,
            (user_id, zip_name)
        ).fetchall()
    except Exception:
        rows = []

    names = [r[0] for r in rows if r and r[0]]
    # Prefer the explicitly requested/wanted project first.
    ordered = [wanted] + [n for n in names if n != wanted]

    base_root = os.path.join(zip_data_dir, zip_name)

    for name in ordered:
        # quick exact-path candidates
        simple_candidates = [
            os.path.join(zip_data_dir, zip_name, name),
            os.path.join(zip_data_dir, name),
        ]
        for cand in simple_candidates:
            if os.path.isdir(cand):
                if is_git_repo(cand):
                    return cand
                nested = bfs_find_repo(cand, max_depth=3)
                if nested:
                    return nested

        # walk deeper under zip_data/<zip_name>
        if os.path.isdir(base_root):
            for root, dirs, files in os.walk(base_root):
                depth = os.path.relpath(root, base_root).count(os.sep)
                if depth > 5:
                    continue
                if os.path.basename(root) == name:
                    if is_git_repo(root):
                        return root
                    nested = bfs_find_repo(root, max_depth=3)
                    if nested:
                        return nested
    return None


def _resolve_from_files_table(conn: sqlite3.Connection,
                              zip_data_dir: str,
                              project_name: str) -> Optional[str]:
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT file_path
            FROM files
            WHERE project_name = ?
            ORDER BY modified DESC
            LIMIT 200
            """,
            (project_name,),
        ).fetchall()
    except Exception:
        return None

    seen: set[str] = set()

    for (fp,) in rows:
        if not fp:
            continue
        parts = fp.replace("\\", "/").strip("/").split("/")
        if not parts:
            continue

        first3 = parts[:3]
        if any(p.lower() == "collaborative" for p in first3):
            use = parts[:3]
        else:
            use = parts[:2]

        cand = os.path.join(zip_data_dir, *use)
        if cand in seen:
            continue
        seen.add(cand)

        if os.path.isdir(cand):
            if is_git_repo(cand):
                return cand
            nested = bfs_find_repo(cand, max_depth=3)
            if nested:
                return nested

    return None


# ------------------------------------------------------------
# 2. user_github table + identity
# ------------------------------------------------------------
def ensure_user_github_table(conn: sqlite3.Connection) -> None:
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
        """,
    )


def load_user_github(conn: sqlite3.Connection, user_id: int) -> Dict[str, set]:
    emails, names = set(), set()
    cur = conn.execute("SELECT email, name FROM user_github WHERE user_id = ?", (user_id,))
    for em, nm in cur.fetchall():
        if em:
            emails.add(em.strip().lower())
        if nm:
            names.add(nm.strip().lower())
    return {"emails": emails, "names": names}


def save_user_github(conn: sqlite3.Connection, user_id: int, emails: List[str], names: List[str]) -> None:
    cur = conn.cursor()
    for em in set(e.strip().lower() for e in emails if e.strip()):
        cur.execute(
            "INSERT OR IGNORE INTO user_github(user_id, email, name) VALUES (?, ?, NULL)",
            (user_id, em),
        )
    for nm in set(n.strip() for n in names if n.strip()):
        cur.execute(
            "INSERT OR IGNORE INTO user_github(user_id, email, name) VALUES (?, NULL, ?)",
            (user_id, nm),
        )
    conn.commit()
    print("\nSaved your identity for future runs")


def collect_repo_authors(repo_dir: str) -> List[Tuple[str, str, int]]:
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


def prompt_user_identity_choice(author_list: List[Tuple[str, str, int]]) -> Tuple[List[str], List[str]]:
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
            an, ae, _ = author_list[i - 1]
            if ae:
                emails.append(ae)
            if an:
                names.append(an)

    extra = input("Add any extra commit emails (comma-separated), or Enter to continue: ").strip()
    if extra:
        emails.extend([e.strip().lower() for e in extra.split(",") if e.strip()])
    return emails, names


# ------------------------------------------------------------
# 3. git parsing
# ------------------------------------------------------------
def _run_git(repo_dir: str, args: List[str]) -> str:
    cmd = ["git", "-C", repo_dir] + args
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        msg = e.output.decode("utf-8", errors="replace")
        print(f"[git error] {' '.join(cmd)}\n{msg}")
        return ""


def read_git_history(repo_dir: str) -> List[dict]:
    fmt = r"%H%x09%an%x09%ae%x09%ad%x09%P%x09%s%x09%B"
    log_numstat = _run_git(
        repo_dir,
        ["log", "--date=iso-strict", f"--pretty=format:{fmt}", "--numstat", "--no-renames"],
    )
    log_namestatus = _run_git(
        repo_dir,
        ["log", "--date=iso-strict", "--name-status", f"--pretty=format:{fmt}"],
    )
    return _parse_git_logs(log_numstat, log_namestatus)


def _parse_git_logs(log_numstat: str, log_namestatus: str) -> List[dict]:
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
                files.append(
                    {
                        "path": path,
                        "additions": additions,
                        "deletions": deletions,
                        "is_binary": is_binary,
                    }
                )

        ns_counts = Counter()
        for row in name_status_map.get(ch, []):
            code = row[0]
            if code.startswith("R"):
                ns_counts["R"] += 1
            elif code in ("A", "M", "D"):
                ns_counts[code] += 1

        commits.append(
            {
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
            }
        )

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

def is_git_repo(path: str) -> bool:
    """
    A directory is a repo if it contains a .git FOLDER,
    or a .git FILE (worktree) pointing to another gitdir.
    """
    git_dir = os.path.join(path, ".git")
    if os.path.isdir(git_dir):
        return True
    if os.path.isfile(git_dir):
        try:
            with open(git_dir, "r", encoding="utf-8", errors="ignore") as f:
                return "gitdir:" in f.read().lower()
        except Exception:
            return False
    return False

def bfs_find_repo(root: str, max_depth: int = 2) -> Optional[str]:
    """
    Breadth-first search to find a nested repo under root, up to max_depth.
    Returns the first directory containing .git.
    """
    if not os.path.isdir(root):
        return None
    if is_git_repo(root):
        return root
    queue: List[Tuple[str, int]] = [(root, 0)]
    while queue:
        path, depth = queue.pop(0)
        if depth > max_depth:
            continue
        try:
            entries = [os.path.join(path, ent) for ent in os.listdir(path)]
        except Exception:
            continue
        for p in entries:
            if os.path.isdir(p):
                if is_git_repo(p):
                    return p
                if depth < max_depth:
                    queue.append((p, depth + 1))
    return None


# ------------------------------------------------------------
# 4. metrics
# ------------------------------------------------------------
def compute_metrics(project: str,
                    path: str,
                    commits: List[dict],
                    aliases: Dict[str, set]) -> dict:
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
        renames += ns.get("R", 0)

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
    last_dt = max((c["authored_at"] for c in commits if c["authored_at"]), default=None)
    l30 = _count_in_last_days(your_commits, 30)
    l90 = _count_in_last_days(your_commits, 90)
    l365 = _count_in_last_days(your_commits, 365)
    longest_streak, current_streak = _streaks(
        [c["authored_at"].date() for c in your_commits if c["authored_at"]]
    )

    dow = Counter()
    hod = Counter()
    for c in your_commits:
        t = c.get("authored_at")
        if t:
            dow[t.strftime("%a")] += 1
            hod[t.hour] += 1
    top_days = ", ".join([d for d, _ in dow.most_common(2)]) if dow else "—"
    top_hours = _top_hours(hod)

    langs_pct = _top_share(lang_loc, label_from_ext=True)
    folders_pct = _top_share(folder_loc, limit=3)
    top_files = [f for f, _ in file_loc.most_common(5)]

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
        },
    }


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
        if (uniq[i] - uniq[i - 1]).days == 1:
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

    def fmt(h): return f"{h:02d}–{(h + 1) % 24:02d}h"

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
    langs = get_languages_for_extension(ext)
    if langs:
        return next(iter(langs))
    return ext.replace(".", "").upper() or "Other"


# ------------------------------------------------------------
# 5. printing
# ------------------------------------------------------------
def print_project_card(m: dict) -> None:
    display_name = m.get("project_name") or m.get("project", "—")
    desc = m.get("desc")

    h = m.get("history", {})
    t = m.get("totals", {})
    l = m.get("loc", {})
    f = m.get("focus", {})

    def dt_str(x):
        try:
            return x.astimezone().strftime("%Y-%m-%d") if x else "—"
        except Exception:
            return "—"

    langs = ", ".join(f.get("languages", [])) or "—"
    folders = ", ".join(f.get("folders", [])) or "—"
    top_files = ", ".join(f.get("top_files", [])) or "—"
    frameworks = ", ".join(f.get("frameworks", [])) or "—"

    active_days = None
    if h.get("first") and h.get("last"):
        try:
            active_days = (h["last"].date() - h["first"].date()).days + 1
        except Exception:
            active_days = None

    def _primary_langs():
        out = []
        for item in f.get("languages", [])[:2]:
            name = item.split()[0] if isinstance(item, str) and item else ""
            if name:
                out.append(name)
        return out

    prim = _primary_langs()

    bits = [
        f"You made {t.get('commits_yours', 0)} of {t.get('commits_all', 0)} commits",
        f"({l.get('net', 0):+,.0f} net lines)",
    ]
    if prim:
        bits.append("mainly in " + " and ".join(prim[:2]))
    if active_days and active_days > 0:
        bits.append(f"over {active_days} day{'s' if active_days != 1 else ''}")
    summary_line = "💡 Summary: " + ", ".join(bits) + "."

    # Only shown if the user rejects the LLM consent
    desc_line = f"Description: {desc}\n" if desc and desc.lower() != "none" else ""

    print(f"""
Project: {display_name}
------------------------------------
{desc_line}Commits: {t.get('commits_all',0)} (You: {t.get('commits_yours',0)} | Co-authored: {t.get('commits_coauth',0)} | Merges: {t.get('merges',0)})
Lines: +{l.get('added',0):,} / -{l.get('deleted',0):,}  →  Net {('+' if l.get('net',0)>=0 else '')}{l.get('net',0):,}
Files: changed {l.get('files_touched',0)}  |  new {l.get('new_files',0)}  |  renames {l.get('renames',0)}

Active: {dt_str(h.get('first'))} → {dt_str(h.get('last'))}   |   L30: {h.get('L30',0)}  L90: {h.get('L90',0)}  L365: {h.get('L365',0)}
Streaks: longest {h.get('longest_streak',0)} days   |   current {h.get('current_streak',0)} days
Focus: {langs}
Frameworks: {frameworks}
Top folders: {folders}
Top files: {top_files}
{summary_line}
""".rstrip())

# ------------------------------------------------------------
# 6. cumulative metrics (from all code)
# ------------------------------------------------------------

STOP = {
    "the","a","an","and","or","to","of","for","in","on","with","by","from","at",
    "is","are","this","that","it","its","my","our","your","we","i","you",
    "app","project","repo","readme","code","using","built","build"
}

def _tokens(s: str) -> list[str]:
    s = (s or "").lower()
    s = re.sub(r"https?://\S+"," ", s)
    s = re.sub(r"[^\w\s+-]"," ", s)
    return [t for t in s.split() if t and t not in STOP and len(t) > 2]

def _try_yake_topk(text: str, k: int = 5) -> list[str]:
    try:
        import yake
        extr = yake.KeywordExtractor(lan="en", n=3, top=k*3)
        cands = [kw for kw,_ in extr.extract_keywords(text)]
        out = []
        for c in cands:
            c = c.strip(" :;.,#'\"()[]{}")
            if c and c not in out:
                out.append(c)
            if len(out) >= k:
                break
        return out
    except Exception:
        return []

def _top_keywords_from_descriptions(descs: list[str], k: int = 5) -> list[str]:
    text = "\n".join(descs).strip()
    if not text:
        return []
    # prefer YAKE if available; otherwise use a simple word counter
    kw = _try_yake_topk(text, k=k)
    if kw:
        return kw
    cnt = Counter(_tokens(text))
    return [w for w,_ in cnt.most_common(k)]

def print_portfolio_summary(all_metrics: list[dict]) -> None:
    if not all_metrics:
        return

    def _commits(m: dict) -> int:
        return int(((m.get("totals") or {}).get("commits_all") or 0))

    n_projects = len(all_metrics)
    total_commits = sum(_commits(m) for m in all_metrics)
    avg_commits = round(total_commits / n_projects, 1) if n_projects else 0.0

    top_proj = max(all_metrics, key=_commits)
    top_proj_name = top_proj.get("project_name") or top_proj.get("project") or "N/A"
    top_proj_commits = _commits(top_proj)

    from collections import Counter
    def _lang_name(s: str) -> str:
        return str(s).split()[0] if s else "Other"

    lang_counts, fw_counts = Counter(), Counter()
    for m in all_metrics:
        langs = (m.get("focus", {}) or {}).get("languages") or []
        if isinstance(langs, dict):
            for lang in langs.keys():
                lang_counts[lang] += 1
        else:
            for lang in langs:
                lang_counts[_lang_name(lang)] += 1
        for fw in (m.get("focus", {}) or {}).get("frameworks") or []:
            fw_counts[str(fw)] += 1

    top_langs = ", ".join([x for x,_ in lang_counts.most_common(3)]) or "—"
    top_fws  = ", ".join([x for x,_ in fw_counts.most_common(3)]) or "—"

    descs = []
    for m in all_metrics:
        d = m.get("desc")
        if not d:
            d = (m.get("desc_readme") or "").splitlines()[0] if m.get("desc_readme") else ""
        if d: descs.append(d)

    top_keywords = _top_keywords_from_descriptions(descs, k=5)

    print("\nCode Collaborative Analysis Summary")
    print("------------------------------------")
    print(f"Total projects: {n_projects}")
    print(f"Total commits: {total_commits}   |   Avg per project: {avg_commits}")
    print(f"Top project by commits: {top_proj_name} ({top_proj_commits} commits)")
    print(f"Top languages overall: {top_langs}")
    print(f"Top frameworks: {top_fws}")
    if top_keywords:
        print(f"Top keywords from your descriptions: {', '.join(top_keywords)}")

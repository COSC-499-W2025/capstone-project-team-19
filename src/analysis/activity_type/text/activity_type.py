import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import time


@dataclass
class ActivityType:
    """Represents an activity type with detection patterns"""
    name: str
    description: str
    patterns: List[str]
    priority: int  

ACTIVITY_TYPES = [
    ActivityType(
        name="Planning",
        description="Planning, outlining, and organizing ideas",
        patterns=[
            r"outline",
            r"plan",
            r"notes",
            r"brainstorm",
            r"structure",
            r"todo",
            r"ideas"
        ],
        priority=1
    ),
    ActivityType(
        name="Research",
        description="Research, sources, and reference materials",
        patterns=[
            r"research",
            r"sources?",
            r"references?",
            r"biblio",
            r"citation",
            r"literature",
            r"reading"
        ],
        priority=2
    ),
    ActivityType(
        name="Drafting",
        description="Initial drafts and working copies",
        patterns=[
            r"draft(?!.*(?:final|rev|edit|v[2-9]))",  # draft but not revised
            r"rough",
            r"initial",
            r"wip",
            r"working",
            r"v1(?:\D|$)",  # v1 specifically
            r"version[_\s]?1"
        ],
        priority=3
    ),
    ActivityType(
        name="Revision",
        description="Revisions, edits, and intermediate versions",
        patterns=[
            r"rev(?:ision)?",
            r"edit(?:ed)?",
            r"v[2-9]",  # v2, v3, etc.
            r"version[_\s]?[2-9]",
            r"draft[_\s]?[2-9]",
            r"(?:second|third|2nd|3rd)",
            r"updated?",
            r"modified"
        ],
        priority=4
    ),
    ActivityType(
        name="Data",
        description="Data collection and analysis files",
        patterns=[
            r"\bdata\b",
            r"\.csv$",
            r"\.xlsx?$",
            r"\banalysis\b",
            r"\bresults?\b",
            r"\bstats?\b"
        ],
        priority=5
    )
]

def detect_activity_type(filename: str)->Optional[str]:
    filename=filename.lower()

    match=[]
    for activity in ACTIVITY_TYPES:
        for pattern in activity.patterns:
            if re.search(pattern, filename):
                match.append(activity)
                break
    
    if not match:
        return None
    
    best_match=min(match, key=lambda a:a.priority)
    return best_match.name

def parse_timestamp(timestamp_str:str)->datetime:
    return datetime.strptime(timestamp_str, "%a %b %d %H:%M:%S %Y")

def analyze_file_timestamps(files: List[Dict])->Dict:
    if not files:
        return{
            'start_date': None,
            'end_date':None,
            'duration_days': 0,
            'files_by_date': []
        }
    
    timestamps=[]
    for f in files:
        created=f.get('created')
        modified=f.get('modified')

        if created:
            timestamps.append(('created', parse_timestamp(created),f))
        if modified:
            timestamps.append(('modified', parse_timestamp(modified),f))       
    if not timestamps:
        return{
            'start_date': None,
            'end_date':None,
            'duration_days': 0,
            'files_by_date': []
        }
    timestamps.sort(key=lambda x:x[1])
    start_date=timestamps[0][1]
    end_date=timestamps[-1][1]
    duration=(end_date-start_date).days

    #sort files by modified date
    files_dates=[]
    for f in files:
        modified_str=f.get('modified')
        modified_dt=parse_timestamp(modified_str)
        files_dates.append({
            'file_name':f.get('file_name'),
            'modified':modified_dt,
            'modified_str':modified_str
        })

    files_dates.sort(key=lambda x:x['modified'])
    return{
            'start_date': start_date,
            'end_date':end_date,
            'duration_days': duration,
            'files_by_date': files_dates
    }

def classify_files_by_activity(files: List[Dict]) -> Dict[str, List[Dict]]:
    classified = {activity.name: [] for activity in ACTIVITY_TYPES}
    classified['Unclassified'] = []

    for f in files:
        filename = f.get('file_name', '')
        activity = detect_activity_type(filename)
        if activity:
            classified[activity].append(f)
        else:
            classified['Unclassified'].append(f)
    return classified


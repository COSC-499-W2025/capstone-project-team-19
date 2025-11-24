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
            r"(?<![a-z])outline(?![a-z])",
            r"(?<![a-z])plan(?![a-z])",
            r"(?<![a-z])notes?(?![a-z])",
            r"brainstorm",
            r"structure",
            r"todo",
            r"(?<![a-z])ideas?(?![a-z])",
            r"proposal",
            r"agenda"
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
            r"reading",
            r"lit[\s_]?review",
            r"\blr\b",
            r"background",
            r"methodology"
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
            r"version[_\s]?1",
            r"draft[_\s]?1",
            r"\bv0(?:\.\d+)?\b",
            r"\bv01\b",
            r"first[\s_]?draft"

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
            r"modified",
            r"rev[_\s]?1",
            r"revision[_\s]?1",
            r"final[_\s]?rev",
            r"draft[_\s]?final"

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
            r"\bstats?\b",
            r"raw[_\s]?data",
            r"cleaned[_\s]?data",
            r"dataset",
            r"features?",
            r"metrics?",
            r"experiment",
            r"run\d+"

        ],
        priority=5
    ),
ActivityType(
    name="Final",
    description="Final submission or main deliverable",
    patterns=[
        r"final",
        r"submission",
        r"main",
        r"complete",
        r"submitted?",
        r"deliverable",
        r"published?",
        r"completed",
        r"finished",
        r"ready",
        r"release",
        r"official",
        r"approved?",
        r"accepted?",
        r"definitive",
        r"ultimate",
        r"last[_\s]?version",
        r"final[_\s]?draft",
        r"final[_\s]?version",
        r"final[_\s]?copy",
        r"final[_\s]?submission",
        r"thesis[_\s]?final",
        r"paper[_\s]?final",
        r"report[_\s]?final",
        r"project[_\s]?final"
    ],
    priority=6
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

def classify_files_by_activity(files: List[Dict], main_file_name: str = None) -> Dict[str, List[Dict]]:
    classified = {activity.name: [] for activity in ACTIVITY_TYPES}
    classified['Unclassified'] = []

    for f in files:
        filename = f.get('file_name', '')

        # Check if this is the main file - always classify as Final
        if main_file_name and filename == main_file_name:
            classified['Final'].append(f)
        else:
            activity = detect_activity_type(filename)
            if activity:
                classified[activity].append(f)
            else:
                classified['Unclassified'].append(f)
    return classified

def get_activity_timeline(files: List[Dict]) -> List[Dict]:
    timeline = []

    for f in files:
        filename = f.get('file_name', '')
        activity = detect_activity_type(filename) or 'Unclassified'

        created_str = f.get('created')
        modified_str = f.get('modified')
        if created_str and modified_str:
            created_dt = parse_timestamp(created_str)
            timeline.append({
                'date': created_dt,
                'date_str': created_str,
                'file_name': filename,
                'activity_type': activity,
                'event': 'created'
            })
        if modified_str:
            modified_dt = parse_timestamp(modified_str)
            timeline.append({
                'date': modified_dt,
                'date_str': modified_str,
                'file_name': filename,
                'activity_type': activity,
                'event': 'modified'
            })
    timeline.sort(key=lambda x: x['date'])
    return timeline

def get_activity_contribution_data(files: List[Dict], main_file_name: str = None) -> Dict:
    timestamp_analysis = analyze_file_timestamps(files)
    classified = classify_files_by_activity(files, main_file_name=main_file_name)
    timeline = get_activity_timeline(files)

    return {
        'timestamp_analysis': {
            'start_date': timestamp_analysis['start_date'],
            'end_date': timestamp_analysis['end_date'],
            'duration_days': timestamp_analysis['duration_days']
        },
        'activity_classification': {
            activity_name: [f['file_name'] for f in files_list]
            for activity_name, files_list in classified.items()
        },
        'timeline': [
            {
                'date': entry['date'],
                'file_name': entry['file_name'],
                'activity_type': entry['activity_type'],
                'event': entry['event']
            }
            for entry in timeline
        ],
        'summary': {
            'total_files': len(files),
            'classified_files': sum(len(files) for activity_name, files in classified.items() if activity_name != 'Unclassified'),
            'activity_counts': {
                activity.name: len(classified[activity.name])
                for activity in ACTIVITY_TYPES
            }
        }
    }

def print_activity(files: List[Dict], project_name: str = "Project", main_file_name: str = None):

    print("\n" + "=" * 80)
    print(f"ACTIVITY TYPE CONTRIBUTION ANALYSIS: {project_name}")
    print("=" * 80)

    print("\nPROJECT DURATION & TIMESTAMPS")
    print("-" * 80)

    timestamp_analysis = analyze_file_timestamps(files)
    start_dt = timestamp_analysis['start_date']
    end_dt = timestamp_analysis['end_date']
    duration = timestamp_analysis['duration_days']

    if start_dt and end_dt:
        print(f"Start Date:     {start_dt.strftime('%B %d, %Y at %I:%M %p')}")
        print(f"End Date:       {end_dt.strftime('%B %d, %Y at %I:%M %p')}")
        print(f"Duration:       {duration} days")

        print("\nFile Timeline (by last modification):")
        for file_info in timestamp_analysis['files_by_date']:
            print(f"  • {file_info['file_name']:40s} → Last edited: {file_info['modified'].strftime('%b %d, %Y')}")
    else:
        print("No timestamp data available")
    print("\n" + "=" * 80)
    print("⏱️  ACTIVITY TIMELINE (Chronological Order)")
    print("-" * 80)

    timeline = get_activity_timeline(files)

    # Override activity type for main file
    for entry in timeline:
        if main_file_name and entry['file_name'] == main_file_name:
            entry['activity_type'] = "Final"

    # Timeline is already sorted by date
    if timeline:
        current_date = None
        for entry in timeline:
            entry_date = entry['date'].strftime('%B %d, %Y')

            # Print date header if changed
            if entry_date != current_date:
                print(f"\n{entry_date}:")
                current_date = entry_date

            time_str = entry['date'].strftime('%I:%M %p')
            print(f"  {time_str} - "
                  f"[{entry['activity_type']}] "
                  f"{entry['file_name']} ({entry['event']})")
    else:
        print("\nNo activity timeline available")

    print("=" * 80 + "\n")
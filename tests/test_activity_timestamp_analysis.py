"""
Unit tests for activity timestamp analysis
Tests timestamp parsing, file timeline generation, and activity timeline
"""

import pytest
from datetime import datetime
from src.analysis.activity_type.text.activity_type import (
    parse_timestamp,
    analyze_file_timestamps,
    get_activity_timeline,
    classify_files_by_activity
)


class TestTimestampParsing:
    """Test timestamp string parsing"""

    def test_parse_valid_timestamp(self):
        """Test parsing a valid timestamp string"""
        timestamp_str = "Sat Nov 22 19:23:46 2025"
        dt = parse_timestamp(timestamp_str)

        assert isinstance(dt, datetime)
        assert dt.year == 2025
        assert dt.month == 11
        assert dt.day == 22
        assert dt.hour == 19
        assert dt.minute == 23
        assert dt.second == 46

    def test_parse_different_dates(self):
        """Test parsing various date strings"""
        test_cases = [
            ("Mon Jan 01 00:00:00 2024", 2024, 1, 1, 0, 0, 0),
            ("Fri Dec 31 23:59:59 2024", 2024, 12, 31, 23, 59, 59),
            ("Wed Jul 04 12:30:45 2025", 2025, 7, 4, 12, 30, 45),
        ]

        for timestamp_str, year, month, day, hour, minute, second in test_cases:
            dt = parse_timestamp(timestamp_str)
            assert dt.year == year
            assert dt.month == month
            assert dt.day == day
            assert dt.hour == hour
            assert dt.minute == minute
            assert dt.second == second


class TestAnalyzeFileTimestamps:
    """Test file timestamp analysis"""

    def test_analyze_single_file(self):
        """Test analyzing timestamps for a single file"""
        files = [
            {
                'file_name': 'test.docx',
                'created': 'Mon Jan 01 10:00:00 2024',
                'modified': 'Mon Jan 01 15:00:00 2024'
            }
        ]

        result = analyze_file_timestamps(files)

        assert result['start_date'] is not None
        assert result['end_date'] is not None
        assert result['duration_days'] == 0  # Same day
        assert len(result['files_by_date']) == 1

    def test_analyze_multiple_files_different_dates(self):
        """Test analyzing files with different modification dates"""
        files = [
            {
                'file_name': 'file1.docx',
                'created': 'Mon Jan 01 10:00:00 2024',
                'modified': 'Mon Jan 01 15:00:00 2024'
            },
            {
                'file_name': 'file2.docx',
                'created': 'Tue Jan 02 10:00:00 2024',
                'modified': 'Wed Jan 10 15:00:00 2024'
            },
            {
                'file_name': 'file3.docx',
                'created': 'Thu Jan 05 10:00:00 2024',
                'modified': 'Thu Jan 05 12:00:00 2024'
            }
        ]

        result = analyze_file_timestamps(files)

        # Should span from Jan 1 to Jan 10 = 9 days
        assert result['start_date'].day == 1
        assert result['end_date'].day == 10
        assert result['duration_days'] == 9

        # Files should be sorted by modification date
        assert len(result['files_by_date']) == 3
        assert result['files_by_date'][0]['file_name'] == 'file1.docx'
        assert result['files_by_date'][1]['file_name'] == 'file3.docx'
        assert result['files_by_date'][2]['file_name'] == 'file2.docx'

    def test_analyze_empty_file_list(self):
        """Test analyzing an empty list of files"""
        result = analyze_file_timestamps([])

        assert result['start_date'] is None
        assert result['end_date'] is None
        assert result['duration_days'] == 0
        assert len(result['files_by_date']) == 0

    def test_analyze_files_without_timestamps(self):
        """Test handling files without timestamp data"""
        files = [
            {
                'file_name': 'file1.docx',
                'created': None,
                'modified': None
            }
        ]

        result = analyze_file_timestamps(files)

        assert result['start_date'] is None
        assert result['end_date'] is None
        assert result['duration_days'] == 0

    def test_duration_calculation(self):
        """Test duration calculation between dates"""
        files = [
            {
                'file_name': 'file1.docx',
                'created': 'Mon Jan 01 10:00:00 2024',
                'modified': 'Mon Jan 01 10:00:00 2024'
            },
            {
                'file_name': 'file2.docx',
                'created': 'Sun Jan 31 10:00:00 2024',
                'modified': 'Sun Jan 31 10:00:00 2024'
            }
        ]

        result = analyze_file_timestamps(files)

        # January 1 to January 31 = 30 days
        assert result['duration_days'] == 30

    def test_files_sorted_by_modified_date(self):
        """Test that files are sorted by modification date in ascending order"""
        files = [
            {
                'file_name': 'last.docx',
                'created': 'Mon Jan 01 10:00:00 2024',
                'modified': 'Fri Jan 05 10:00:00 2024'
            },
            {
                'file_name': 'first.docx',
                'created': 'Mon Jan 01 10:00:00 2024',
                'modified': 'Mon Jan 01 10:00:00 2024'
            },
            {
                'file_name': 'middle.docx',
                'created': 'Mon Jan 01 10:00:00 2024',
                'modified': 'Wed Jan 03 10:00:00 2024'
            }
        ]

        result = analyze_file_timestamps(files)

        assert result['files_by_date'][0]['file_name'] == 'first.docx'
        assert result['files_by_date'][1]['file_name'] == 'middle.docx'
        assert result['files_by_date'][2]['file_name'] == 'last.docx'


class TestActivityTimeline:
    """Test activity timeline generation"""

    def test_timeline_with_single_file(self):
        """Test generating timeline for a single file"""
        files = [
            {
                'file_name': 'draft.docx',
                'created': 'Mon Jan 01 10:00:00 2024',
                'modified': 'Mon Jan 01 15:00:00 2024'
            }
        ]

        timeline = get_activity_timeline(files)

        # Should have 2 events: created and modified
        assert len(timeline) == 2

        # Check created event
        assert timeline[0]['file_name'] == 'draft.docx'
        assert timeline[0]['activity_type'] == 'Drafting'
        assert timeline[0]['event'] == 'created'

        # Check modified event
        assert timeline[1]['file_name'] == 'draft.docx'
        assert timeline[1]['activity_type'] == 'Drafting'
        assert timeline[1]['event'] == 'modified'

    def test_timeline_chronological_order(self):
        """Test that timeline events are in chronological order"""
        files = [
            {
                'file_name': 'outline.docx',
                'created': 'Mon Jan 01 10:00:00 2024',
                'modified': 'Mon Jan 01 11:00:00 2024'
            },
            {
                'file_name': 'draft.docx',
                'created': 'Mon Jan 01 09:00:00 2024',  # Earlier
                'modified': 'Mon Jan 01 12:00:00 2024'
            }
        ]

        timeline = get_activity_timeline(files)

        # Should be sorted chronologically
        assert timeline[0]['event'] == 'created'
        assert timeline[0]['file_name'] == 'draft.docx'
        assert timeline[0]['date'].hour == 9

        assert timeline[1]['event'] == 'created'
        assert timeline[1]['file_name'] == 'outline.docx'
        assert timeline[1]['date'].hour == 10

        assert timeline[2]['event'] == 'modified'
        assert timeline[2]['file_name'] == 'outline.docx'
        assert timeline[2]['date'].hour == 11

        assert timeline[3]['event'] == 'modified'
        assert timeline[3]['file_name'] == 'draft.docx'
        assert timeline[3]['date'].hour == 12

    def test_timeline_activity_type_detection(self):
        """Test that timeline correctly identifies activity types"""
        files = [
            {
                'file_name': 'project_outline.docx',
                'created': 'Mon Jan 01 10:00:00 2024',
                'modified': 'Mon Jan 01 10:00:00 2024'
            },
            {
                'file_name': 'research_notes.txt',
                'created': 'Mon Jan 02 10:00:00 2024',
                'modified': 'Mon Jan 02 10:00:00 2024'
            },
            {
                'file_name': 'draft_v1.docx',
                'created': 'Mon Jan 03 10:00:00 2024',
                'modified': 'Mon Jan 03 10:00:00 2024'
            }
        ]

        timeline = get_activity_timeline(files)

        # Find events by filename
        outline_events = [e for e in timeline if e['file_name'] == 'project_outline.docx']
        research_events = [e for e in timeline if e['file_name'] == 'research_paper.txt']  
        draft_events = [e for e in timeline if e['file_name'] == 'draft_v1.docx']

        assert all(e['activity_type'] == 'Planning' for e in outline_events)
        assert all(e['activity_type'] == 'Research' for e in research_events)
        assert all(e['activity_type'] == 'Drafting' for e in draft_events)

    def test_timeline_unclassified_files(self):
        """Test timeline with unclassified files"""
        files = [
            {
                'file_name': 'random_file.docx',
                'created': 'Mon Jan 01 10:00:00 2024',
                'modified': 'Mon Jan 01 10:00:00 2024'
            }
        ]

        timeline = get_activity_timeline(files)

        assert len(timeline) == 2
        assert all(e['activity_type'] == 'Unclassified' for e in timeline)

    def test_timeline_empty_files(self):
        """Test timeline with empty file list"""
        timeline = get_activity_timeline([])

        assert len(timeline) == 0
        assert isinstance(timeline, list)

    def test_timeline_date_objects(self):
        """Test that timeline entries have proper datetime objects"""
        files = [
            {
                'file_name': 'test.docx',
                'created': 'Mon Jan 01 10:00:00 2024',
                'modified': 'Mon Jan 01 15:00:00 2024'
            }
        ]

        timeline = get_activity_timeline(files)

        for entry in timeline:
            assert 'date' in entry
            assert isinstance(entry['date'], datetime)
            assert 'date_str' in entry
            assert isinstance(entry['date_str'], str)


class TestIntegrationScenarios:
    """Test realistic scenarios combining multiple functions"""

    def test_complete_project_workflow(self):
        """Test a complete project workflow from planning to final revision"""
        files = [
            {
                'file_name': 'project_outline.docx',
                'created': 'Mon Jan 01 09:00:00 2024',
                'modified': 'Mon Jan 01 10:00:00 2024'
            },
            {
                'file_name': 'research_paper.txt',  
                'created': 'Tue Jan 02 10:00:00 2024',
                'modified': 'Tue Jan 02 15:00:00 2024'
            },
            {
                'file_name': 'draft_v1.docx',
                'created': 'Wed Jan 03 09:00:00 2024',
                'modified': 'Wed Jan 03 17:00:00 2024'
            },
            {
                'file_name': 'essay_v2.docx',
                'created': 'Thu Jan 04 10:00:00 2024',
                'modified': 'Thu Jan 04 16:00:00 2024'
            },
            {
                'file_name': 'final_version.docx',
                'created': 'Fri Jan 05 11:00:00 2024',
                'modified': 'Fri Jan 05 14:00:00 2024'
            }
        ]

        # Test timestamp analysis
        timestamp_analysis = analyze_file_timestamps(files)
        assert timestamp_analysis['duration_days'] == 4  # Jan 1-5 = 4 days
        assert len(timestamp_analysis['files_by_date']) == 5

        # Test classification
        classified = classify_files_by_activity(files)
        assert len(classified['Planning']) == 1
        assert len(classified['Research']) == 1
        assert len(classified['Drafting']) == 1
        assert len(classified['Revision']) == 1

        # Test timeline
        timeline = get_activity_timeline(files)
        assert len(timeline) == 10  # 5 files × 2 events each

        # Verify progression
        activity_sequence = [e['activity_type'] for e in timeline[::2]]  # Every other (created events)
        assert activity_sequence == ['Planning', 'Research', 'Drafting', 'Revision', 'Unclassified']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

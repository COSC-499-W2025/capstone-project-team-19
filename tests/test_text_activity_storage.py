"""
Tests for text activity type contribution storage
"""

import pytest
import sqlite3
from datetime import datetime
import src.db as db
from src.analysis.activity_type.text.activity_type import get_activity_contribution_data


@pytest.fixture
def test_db():
    """Create an in-memory database for testing"""
    conn = db.connect(":memory:")
    db.init_schema(conn)
    yield conn
    conn.close()


def test_store_and_retrieve_activity_contribution(test_db):
    """Test storing and retrieving activity contribution data"""
    # Create a test user and project classification
    user_id = db.get_or_create_user(test_db, "testuser", "test@example.com")

    db.record_project_classification(
        test_db,
        user_id=user_id,
        zip_path="/path/to/test.zip",
        zip_name="test",
        project_name="TestProject",
        classification="individual",
        when=datetime.now()
    )

    classification_id = db.get_classification_id(test_db, user_id, "TestProject")
    assert classification_id is not None

    # Sample activity data (simulating what get_activity_contribution_data() returns)
    sample_files = [
        {
            'file_name': 'outline.docx',
            'file_path': 'project/outline.docx',
            'created': 'Mon Jan 01 09:00:00 2024',
            'modified': 'Mon Jan 01 10:00:00 2024',
            'file_type': 'text'
        },
        {
            'file_name': 'draft.docx',
            'file_path': 'project/draft.docx',
            'created': 'Tue Jan 02 09:00:00 2024',
            'modified': 'Tue Jan 02 15:00:00 2024',
            'file_type': 'text'
        }
    ]

    activity_data = get_activity_contribution_data(sample_files)

    # Store the activity contribution data
    db.store_text_activity_contribution(test_db, classification_id, activity_data)

    # Retrieve and verify
    retrieved = db.get_text_activity_contribution(test_db, classification_id)

    assert retrieved is not None
    assert retrieved['classification_id'] == classification_id
    assert retrieved['summary']['total_files'] == 2
    assert 'Planning' in retrieved['activity_classification']
    assert 'Drafting' in retrieved['activity_classification']
    assert len(retrieved['timeline']) > 0


def test_update_existing_activity_contribution(test_db):
    """Test that updating existing data works correctly"""
    user_id = db.get_or_create_user(test_db, "testuser", "test@example.com")

    db.record_project_classification(
        test_db,
        user_id=user_id,
        zip_path="/path/to/test.zip",
        zip_name="test",
        project_name="TestProject",
        classification="individual"
    )

    classification_id = db.get_classification_id(test_db, user_id, "TestProject")

    # First store
    activity_data1 = {
        'timestamp_analysis': {
            'start_date': datetime(2024, 1, 1),
            'end_date': datetime(2024, 1, 5),
            'duration_days': 4
        },
        'activity_classification': {
            'Planning': ['file1.txt'],
            'Drafting': ['file2.txt']
        },
        'timeline': [
            {
                'date': datetime(2024, 1, 1),
                'file_name': 'file1.txt',
                'activity_type': 'Planning',
                'event': 'created'
            }
        ],
        'summary': {
            'total_files': 2,
            'classified_files': 2,
            'activity_counts': {'Planning': 1, 'Drafting': 1}
        }
    }

    db.store_text_activity_contribution(test_db, classification_id, activity_data1)

    # Update with new data
    activity_data2 = {
        'timestamp_analysis': {
            'start_date': datetime(2024, 1, 1),
            'end_date': datetime(2024, 1, 10),
            'duration_days': 9
        },
        'activity_classification': {
            'Planning': ['file1.txt'],
            'Drafting': ['file2.txt'],
            'Revision': ['file3.txt']
        },
        'timeline': [
            {
                'date': datetime(2024, 1, 1),
                'file_name': 'file1.txt',
                'activity_type': 'Planning',
                'event': 'created'
            },
            {
                'date': datetime(2024, 1, 10),
                'file_name': 'file3.txt',
                'activity_type': 'Revision',
                'event': 'created'
            }
        ],
        'summary': {
            'total_files': 3,
            'classified_files': 3,
            'activity_counts': {'Planning': 1, 'Drafting': 1, 'Revision': 1}
        }
    }

    db.store_text_activity_contribution(test_db, classification_id, activity_data2)

    # Retrieve and verify it was updated
    retrieved = db.get_text_activity_contribution(test_db, classification_id)

    assert retrieved['summary']['total_files'] == 3
    assert retrieved['timestamp_analysis']['duration_days'] == 9
    assert 'Revision' in retrieved['activity_classification']


def test_retrieve_nonexistent_activity_contribution(test_db):
    """Test retrieving data that doesn't exist returns None"""
    result = db.get_text_activity_contribution(test_db, 999999)
    assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

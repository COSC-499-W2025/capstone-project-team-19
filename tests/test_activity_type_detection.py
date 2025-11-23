"""
Unit tests for activity type detection functionality
Tests the pattern matching and classification of files by activity type
"""

import pytest
from src.analysis.activity_type.text.activity_type import (
    detect_activity_type,
    classify_files_by_activity,
    ACTIVITY_TYPES
)

class TestActivityTypeDetection:
    """Test activity type detection based on filename patterns"""

    def test_detect_planning_files(self):
        """Test detection of planning-related files"""
        assert detect_activity_type("project_outline.docx") == "Planning"
        assert detect_activity_type("project_plan.pdf") == "Planning"
        assert detect_activity_type("brainstorm_notes.txt") == "Planning"
        assert detect_activity_type("TODO_list.md") == "Planning"
        assert detect_activity_type("project_ideas.docx") == "Planning"
        assert detect_activity_type("proposal_v1.docx") == "Planning"
        assert detect_activity_type("meeting_agenda.pdf") == "Planning"

    def test_detect_research_files(self):
        """Test detection of research-related files"""
        assert detect_activity_type("literature_review.docx") == "Research"
        assert detect_activity_type("research_paper.txt") == "Research" 
        assert detect_activity_type("sources.pdf") == "Research"
        assert detect_activity_type("references.bib") == "Research"
        assert detect_activity_type("bibliography.docx") == "Research"
        assert detect_activity_type("lr.docx") == "Research"
        assert detect_activity_type("background_research.pdf") == "Research"
        assert detect_activity_type("methodology.docx") == "Research"

    def test_detect_drafting_files(self):
        """Test detection of initial draft files"""
        assert detect_activity_type("draft_essay.docx") == "Drafting"
        assert detect_activity_type("rough_draft.txt") == "Drafting"
        assert detect_activity_type("initial_report.docx") == "Drafting"
        assert detect_activity_type("essay_v1.docx") == "Drafting"
        assert detect_activity_type("version_1.pdf") == "Drafting"
        assert detect_activity_type("draft_1.docx") == "Drafting"
        assert detect_activity_type("first_draft.txt") == "Drafting"
        assert detect_activity_type("wip_document.docx") == "Drafting"
        assert detect_activity_type("working_copy.txt") == "Drafting"

    def test_detect_revision_files(self):
        """Test detection of revision and edited files"""
        assert detect_activity_type("essay_v2.docx") == "Revision"
        assert detect_activity_type("revised_essay.txt") == "Revision"  
        assert detect_activity_type("edited_version.docx") == "Revision"
        assert detect_activity_type("version_3.pdf") == "Revision"
        assert detect_activity_type("final_revision.docx") == "Revision"
        assert detect_activity_type("final_rev.pdf") == "Revision"
        assert detect_activity_type("updated_report.docx") == "Revision"
        assert detect_activity_type("rev_1.txt") == "Revision"

    def test_detect_data_files(self):
        """Test detection of data-related files"""
        assert detect_activity_type("survey_data.csv") == "Data"
        assert detect_activity_type("results.xlsx") == "Data"
        assert detect_activity_type("analysis_data.csv") == "Data"
        assert detect_activity_type("statistics.xlsx") == "Data"
        assert detect_activity_type("raw_data.csv") == "Data"
        assert detect_activity_type("cleaned_data.xlsx") == "Data"
        assert detect_activity_type("dataset.csv") == "Data" 
        assert detect_activity_type("experiment_results.xlsx") == "Data"
        assert detect_activity_type("metrics.csv") == "Data"

    def test_no_match_returns_none(self):
        """Test that files without matching patterns return None"""
        assert detect_activity_type("random_file.docx") is None
        assert detect_activity_type("untitled.txt") is None
        assert detect_activity_type("document.pdf") is None

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive"""
        assert detect_activity_type("DRAFT.docx") == "Drafting"
        assert detect_activity_type("Draft.docx") == "Drafting"
        assert detect_activity_type("RESEARCH.txt") == "Research" 
        assert detect_activity_type("Research.txt") == "Research"

    def test_priority_based_matching(self):
        """Test that higher priority patterns take precedence"""
        # Planning has priority 1, should match first even if other patterns exist
        assert detect_activity_type("outline_draft.docx") == "Planning"

        # Research has priority 2, should match before Drafting (priority 3)
        assert detect_activity_type("research_v1.docx") == "Research"

    def test_draft_vs_final_distinction(self):
        """Test that 'draft' without revision markers is classified as Drafting"""
        # Pure draft should be Drafting
        assert detect_activity_type("essay_draft.docx") == "Drafting"

        # Draft with revision markers should be Revision
        assert detect_activity_type("draft_final.docx") == "Revision"
        assert detect_activity_type("draft_v2.docx") == "Revision"


class TestClassifyFilesByActivity:
    """Test classification of multiple files by activity type"""

    def test_classify_mixed_files(self):
        """Test classifying a mix of different file types"""
        files = [
            {'file_name': 'project_outline.docx', 'file_path': 'path/outline.docx'},
            {'file_name': 'research_paper.txt', 'file_path': 'path/research.txt'},
            {'file_name': 'draft_v1.docx', 'file_path': 'path/draft.docx'},
            {'file_name': 'essay_v2.pdf', 'file_path': 'path/essay_v2.pdf'},
            {'file_name': 'data.csv', 'file_path': 'path/data.csv'},
            {'file_name': 'random.docx', 'file_path': 'path/random.docx'},
        ]

        classified = classify_files_by_activity(files)

        assert len(classified['Planning']) == 1
        assert classified['Planning'][0]['file_name'] == 'project_outline.docx'

        assert len(classified['Research']) == 1
        assert classified['Research'][0]['file_name'] == 'research_paper.txt' 

        assert len(classified['Drafting']) == 1
        assert classified['Drafting'][0]['file_name'] == 'draft_v1.docx'

        assert len(classified['Revision']) == 1
        assert classified['Revision'][0]['file_name'] == 'essay_v2.pdf'

        assert len(classified['Data']) == 1
        assert classified['Data'][0]['file_name'] == 'data.csv'

        assert len(classified['Unclassified']) == 1
        assert classified['Unclassified'][0]['file_name'] == 'random.docx'

    def test_classify_empty_list(self):
        """Test classifying an empty list of files"""
        classified = classify_files_by_activity([])

        # All categories should exist but be empty
        for activity in ACTIVITY_TYPES:
            assert activity.name in classified
            assert len(classified[activity.name]) == 0
        assert len(classified['Unclassified']) == 0

    def test_all_unclassified(self):
        """Test when all files are unclassified"""
        files = [
            {'file_name': 'file1.docx', 'file_path': 'path/file1.docx'},
            {'file_name': 'file2.txt', 'file_path': 'path/file2.txt'},
        ]

        classified = classify_files_by_activity(files)

        # All activity types should be empty
        for activity in ACTIVITY_TYPES:
            assert len(classified[activity.name]) == 0

        # Unclassified should have all files
        assert len(classified['Unclassified']) == 2


class TestActivityTypePatterns:
    """Test specific pattern edge cases"""

    def test_version_number_patterns(self):
        """Test various version numbering patterns"""
        # v1 should be Drafting
        assert detect_activity_type("report_v1.docx") == "Drafting"
        assert detect_activity_type("essay_v1.txt") == "Drafting"

        # v2+ should be Revision
        assert detect_activity_type("report_v2.docx") == "Revision"
        assert detect_activity_type("essay_v3.txt") == "Revision"
        assert detect_activity_type("paper_v9.pdf") == "Revision"

    def test_csv_xlsx_detection(self):
        """Test that CSV and Excel files are detected as Data"""
        assert detect_activity_type("survey.csv") == "Data"
        assert detect_activity_type("results.xlsx") == "Data"
        assert detect_activity_type("analysis.xls") == "Data"

    def test_complex_filenames(self):
        """Test detection with complex, realistic filenames"""
        assert detect_activity_type("COSC_499_Project_Outline_v1.docx") == "Planning"
        assert detect_activity_type("Literature_Review_Draft_2.pdf") == "Research"
        assert detect_activity_type("Final_Essay_Revision_3.docx") == "Revision"
        assert detect_activity_type("Survey_Results_Raw_Data.csv") == "Data"

    def test_special_characters_in_filename(self):
        """Test filenames with special characters"""
        assert detect_activity_type("project-outline.docx") == "Planning"
        assert detect_activity_type("draft_essay (1).txt") == "Drafting"
        assert detect_activity_type("essay.v2.pdf") == "Revision"  



if __name__ == "__main__":
    pytest.main([__file__, "-v"])

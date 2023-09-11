import datetime as dt

from cg.models.fluffy import FluffySampleSheetHeader


def test_fluffy_sample_sheet_entry(fluffy_sample_sheet_entry):
    """
    Test that a FluffySampleSheetEntry instance is created with the correct attributes.
    """
    assert fluffy_sample_sheet_entry.flow_cell_id == "FC1"
    assert fluffy_sample_sheet_entry.lane == 1
    assert fluffy_sample_sheet_entry.sample_internal_id == "sample1"
    assert fluffy_sample_sheet_entry.index == "ATCG"
    assert fluffy_sample_sheet_entry.index2 == "CGAT"
    assert fluffy_sample_sheet_entry.sample_name == "Sample 1"
    assert fluffy_sample_sheet_entry.sample_project == "Project 1"
    assert fluffy_sample_sheet_entry.exclude == False
    assert fluffy_sample_sheet_entry.library_nM == 10.0
    assert fluffy_sample_sheet_entry.sequencing_date == dt.date(2022, 1, 1)


def test_fluffy_sample_sheet(fluffy_sample_sheet):
    """
    Test that a FluffySampleSheet instance is created with the correct attributes.
    """
    assert fluffy_sample_sheet.header == list(FluffySampleSheetHeader)
    assert len(fluffy_sample_sheet.entries) == 2


def test_fluffy_sample_sheet_file(fluffy_sample_sheet_file):
    """
    Test that a FluffySampleSheet instance can be written to a file and read back correctly.
    """
    with fluffy_sample_sheet_file.open("r") as infile:
        lines = infile.readlines()

    assert lines[0].strip() == ",".join(
        [column.value for column in FluffySampleSheetHeader]
    )  # Check header
    assert len(lines) == 3  # Check number of lines

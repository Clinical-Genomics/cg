import datetime as dt
from pathlib import Path

import pytest

from cg.models.fluffy import FluffySampleSheet, FluffySampleSheetEntry, FluffySampleSheetHeader


@pytest.fixture
def fluffy_sample_sheet_entry():
    return FluffySampleSheetEntry(
        flow_cell_id="FC1",
        lane=1,
        sample_internal_id="sample1",
        index="ATCG",
        index2="CGAT",
        sample_name="Sample 1",
        sample_project="Project 1",
        exclude=False,
        library_nM=10.0,
        sequencing_date=dt.date(2022, 1, 1),
    )


@pytest.fixture
def fluffy_sample_sheet_entries():
    return [
        FluffySampleSheetEntry(
            flow_cell_id="FC1",
            lane=1,
            sample_internal_id="sample1",
            index="ATCG",
            index2="CGAT",
            sample_name="Sample 1",
            sample_project="Project 1",
            exclude=False,
            library_nM=10.0,
            sequencing_date=dt.date(2022, 1, 1),
        ),
        FluffySampleSheetEntry(
            flow_cell_id="FC1",
            lane=2,
            sample_internal_id="sample2",
            index="CGAT",
            index2="ATCG",
            sample_name="Sample 2",
            sample_project="Project 2",
            exclude=True,
            library_nM=20.0,
            sequencing_date=dt.date(2022, 1, 1),
        ),
    ]


@pytest.fixture
def fluffy_sample_sheet(fluffy_sample_sheet_entries):
    return FluffySampleSheet(header=FluffySampleSheetHeader, entries=fluffy_sample_sheet_entries)


@pytest.fixture
def fluffy_sample_sheet_file(fluffy_sample_sheet):
    out_path = Path("test_sample_sheet.csv")
    fluffy_sample_sheet.write_sample_sheet(out_path)
    yield out_path
    out_path.unlink()  # Clean up the test file

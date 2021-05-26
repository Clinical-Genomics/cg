from pathlib import Path

from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator
from cgmodels.demultiplex.sample_sheet import SampleSheet, get_sample_sheet


def test_convert_to_sheet(novaseq_sample_sheet_object: SampleSheetCreator, project_dir: Path):
    # GIVEN a sample sheet object populated with samples
    assert novaseq_sample_sheet_object.lims_samples

    # WHEN converting to sample sheet
    sample_sheet: str = novaseq_sample_sheet_object.construct_sample_sheet()

    # THEN assert a correctly formatted sample sheet was created
    sample_sheet_object: SampleSheet = get_sample_sheet(sample_sheet=sample_sheet, sheet_type="S4")
    assert sample_sheet_object.samples

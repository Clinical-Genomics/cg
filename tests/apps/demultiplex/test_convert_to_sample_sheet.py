from pathlib import Path

from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator
from cgmodels.demultiplex.sample_sheet import SampleSheet, get_sample_sheet


def test_convert_to_bcl2fastq_sheet(
    novaseq_bcl2fastq_sample_sheet_object: SampleSheetCreator, project_dir: Path
):
    # GIVEN a sample sheet object populated with samples
    assert novaseq_bcl2fastq_sample_sheet_object.lims_samples

    # WHEN converting to a sample sheet
    sample_sheet: str = novaseq_bcl2fastq_sample_sheet_object.construct_sample_sheet()

    # THEN assert a correctly formatted sample sheet was created
    sample_sheet_object: SampleSheet = get_sample_sheet(
        sample_sheet=sample_sheet,
        sheet_type="S4",
        bcl_converter=novaseq_bcl2fastq_sample_sheet_object.bcl_converter,
    )
    assert sample_sheet_object.samples


def test_convert_to_dragen_sheet(
    novaseq_dragen_sample_sheet_object: SampleSheetCreator, project_dir: Path
):
    # GIVEN a sample sheet object populated with samples
    assert novaseq_dragen_sample_sheet_object.lims_samples

    # WHEN converting to a sample sheet
    sample_sheet: str = novaseq_dragen_sample_sheet_object.construct_sample_sheet()

    # THEN assert a correctly formatted sample sheet was created
    sample_sheet_object: SampleSheet = get_sample_sheet(
        sample_sheet=sample_sheet,
        sheet_type="S4",
        bcl_converter=novaseq_dragen_sample_sheet_object.bcl_converter,
    )
    assert sample_sheet_object.samples

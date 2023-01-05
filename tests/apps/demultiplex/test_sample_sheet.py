from typing import List

from cg.apps.demultiplex.sample_sheet import dummy_sample, index
from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator
from cg.apps.lims.samplesheet import LimsFlowcellSample


def test_get_valid_indexes():
    # GIVEN a sample sheet api

    # WHEN fetching the indexes
    indexes: List[Index] = index.get_valid_indexes()

    # THEN assert that the indexes are correct
    assert len(indexes) > 0
    assert isinstance(indexes[0], Index)


def test_get_dummy_sample_name():
    # GIVEN a raw sample name from the index file
    raw_sample_name = "D10 - D710-D504 (TCCGCGAA-GGCTCTGA)"

    # WHEN converting it to a dummy sample name
    dummy_sample_name: str = dummy_sample.dummy_sample_name(raw_sample_name)

    # THEN assert the correct name was created
    assert dummy_sample_name == "D10---D710-D504--TCCGCGAA-GGCTCTGA-"


def test_get_dummy_sample(flow_cell_id: str, index_obj: Index):
    # GIVEN some dummy sample data

    # WHEN creating the dummy sample for a bcl2fastq samplesheet
    dummy_sample_obj: LimsFlowcellSample = dummy_sample.dummy_sample(
        flowcell=flow_cell_id,
        dummy_index=index_obj.sequence,
        lane=1,
        name=index_obj.name,
        bcl_converter="bcl2fastq",
    )

    # THEN assert the sample id was correct
    assert dummy_sample_obj.sample_id == dummy_sample.dummy_sample_name(index_obj.name)


def test_get_project_name():
    # GIVEN a raw string
    raw = "project name"

    # WheN parsing the project name
    project_name = SampleSheetCreator.get_project_name(raw)

    # THEN assert the correct project name was returned
    assert project_name == "project"

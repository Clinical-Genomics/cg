from typing import List

from cg.apps.demultiplex.novaseq_sample_sheet import SampleSheet
from cg.apps.demultiplex.sample_sheet import create_sample_sheet
from cg.apps.lims import LimsAPI
from cg.apps.lims.samplesheet import LimsFlowcellSample, sample_sheet
from cg.models.demultiplex.run_parameters import RunParameters
from cg.models.demultiplex.valid_indexes import Index

# def test_create_sample_sheet_novaseq(
#     lims_novaseq_samples: List[LimsFlowcellSample], lims_api: LimsAPI, mocker
# ):
#     """Test the create sample sheet function"""
#     # GIVEN that the lims returns some sample information
#     mocker.patch(
#         # api_call is from slow.py but imported to main.py
#         "cg.apps.demultiplex.sample_sheet.sample_sheet",
#         return_value=lims_novaseq_samples,
#     )
#     # WHEN running create_sample_sheet
#     res = create_sample_sheet(lims=lims_api, flowcell_type="novaseq", flowcell_name="hello")
#
#     print(res)
#     assert 0


def test_get_valid_indexes():
    # GIVEN a sample sheet api

    # WHEN fetching the indexes
    indexes: List[Index] = SampleSheet.get_valid_indexes()

    # THEN assert that the indexes are correct
    assert len(indexes) > 0
    assert isinstance(indexes[0], Index)


def test_get_dummy_sample_name():
    # GIVEN a raw sample name from the index file
    raw_sample_name = "D10 - D710-D504 (TCCGCGAA-GGCTCTGA)"

    # WHEN converting it to a dummy sample name
    dummy_sample_name: str = SampleSheet.dummy_sample_name(raw_sample_name)

    # THEN assert the correct name was created
    assert dummy_sample_name == "D10---D710-D504--TCCGCGAA-GGCTCTGA-"


def test_get_dummy_sample(flowcell_name: str, index_obj: Index):
    # GIVEN some dummy sample data

    # WHEN creating the dummy sample
    dummy_sample: LimsFlowcellSample = SampleSheet.dummy_sample(
        flowcell=flowcell_name, dummy_index=index_obj.sequence, lane=1, name=index_obj.name
    )

    # THEN assert the sample id was correct
    assert dummy_sample.sample_id == SampleSheet.dummy_sample_name(index_obj.name)


def test_get_project_name():
    # GIVEN a raw string
    raw = "project name"

    # WheN parsing the project name
    project_name = SampleSheet.get_project_name(raw)

    # THEN assert the correct project name was returned
    assert project_name == "project"

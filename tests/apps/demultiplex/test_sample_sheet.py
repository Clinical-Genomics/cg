from typing import List

from cg.apps.demultiplex.sample_sheet import create_sample_sheet
from cg.apps.lims import LimsAPI
from cg.apps.lims.samplesheet import LimsFlowcellSample, sample_sheet


def test_create_sample_sheet_novaseq(
    lims_novaseq_samples: List[LimsFlowcellSample], lims_api: LimsAPI, mocker
):
    """Test the create sample sheet function"""
    # GIVEN that the lims returns some sample information
    mocker.patch(
        # api_call is from slow.py but imported to main.py
        "cg.apps.demultiplex.sample_sheet.sample_sheet",
        return_value=lims_novaseq_samples,
    )
    # WHEN running create_sample_sheet
    res = create_sample_sheet(lims=lims_api, flowcell_type="novaseq", flowcell_name="hello")

    print(res)
    assert 0

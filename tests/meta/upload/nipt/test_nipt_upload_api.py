from cg.constants.nipt import Q30_THRESHOLD
from cg.meta.upload.nipt import NiptUploadAPI
from cg.models.cg_config import CGConfig


def test_flowcell_passed_qc_value(case_id: str, nipt_upload_api_context: CGConfig):

    # GIVEN a NiptUploadAPI context with a case that has been sequenced
    nipt_upload_api: NiptUploadAPI = NiptUploadAPI(nipt_upload_api_context)

    # WHEN checking the Q30 and read values on the flow cell
    flowcell_qc_value: bool = nipt_upload_api.flowcell_passed_qc_value(
        case_id=case_id, q30_threshold=Q30_THRESHOLD
    )

    # THEN the successful flow cell shall pass and
    assert flowcell_qc_value


def test_flowcell_failed_qc_value(
    nipt_upload_api_failed_fc_context: CGConfig, case_id: str, sample_id: str
):

    # GIVEN a NiptUploadAPI context with a case that has been sequenced, however the case is lacking reads
    nipt_upload_api: NiptUploadAPI = NiptUploadAPI(nipt_upload_api_failed_fc_context)

    # WHEN checking the Q30 and read values on the flowcell
    flowcell_qc_pass: bool = nipt_upload_api.flowcell_passed_qc_value(
        case_id=case_id, q30_threshold=Q30_THRESHOLD
    )

    # THEN the failed flow cell should have not been passed
    assert not flowcell_qc_pass

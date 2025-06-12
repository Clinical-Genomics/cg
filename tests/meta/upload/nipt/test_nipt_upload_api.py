from cg.constants.nipt import Q30_THRESHOLD
from cg.meta.upload.nipt import NiptUploadAPI
from cg.models.cg_config import CGConfig


def test_sequencing_run_passed_qc_value(
    case_id_for_sample_on_multiple_flow_cells: str, nipt_upload_api_context: CGConfig
):
    # GIVEN a NiptUploadAPI context with a case that has been sequenced
    nipt_upload_api: NiptUploadAPI = NiptUploadAPI(nipt_upload_api_context)

    # WHEN checking the Q30 and read values on the flow cell
    sequencing_run_qc_value: bool = nipt_upload_api.sequencing_run_passed_qc_value(
        case_id=case_id_for_sample_on_multiple_flow_cells, q30_threshold=Q30_THRESHOLD
    )

    # THEN the successful flow cell shall pass
    assert sequencing_run_qc_value


def test_sequencing_run_failed_qc_value(
    nipt_upload_api_failed_fc_context: CGConfig,
    case_id_for_sample_on_multiple_flow_cells: str,
    sample_id: str,
):
    # GIVEN a NiptUploadAPI context with a case that has been sequenced, however the case is lacking reads
    nipt_upload_api: NiptUploadAPI = NiptUploadAPI(nipt_upload_api_failed_fc_context)

    # WHEN checking the Q30 and read values on the sequencing run
    sequencing_run_qc_pass: bool = nipt_upload_api.sequencing_run_passed_qc_value(
        case_id=case_id_for_sample_on_multiple_flow_cells, q30_threshold=Q30_THRESHOLD
    )

    # THEN the failed sequencing run should have not been passed
    assert not sequencing_run_qc_pass

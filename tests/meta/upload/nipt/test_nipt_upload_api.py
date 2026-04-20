from pathlib import Path
from unittest.mock import create_autospec

from housekeeper.store.models import File
from pytest_mock import MockerFixture

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.nipt import Q30_THRESHOLD
from cg.meta.upload.nipt import NiptUploadAPI
from cg.meta.upload.nipt.models import StatinaUploadFiles
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


def test_get_statina_files(nipt_upload_api_context: CGConfig, mocker: MockerFixture):
    # GIVEN a NiptUploadAPI
    nipt_upload_api = NiptUploadAPI(nipt_upload_api_context)

    # GIVEN that files exist in Housekeeper
    housekeeper_api = create_autospec(HousekeeperAPI)

    def mock_get_file(bundle_name: str, tags: list[str]):
        if tags == ["nipt", "metrics"]:
            return create_autospec(File, path="results/file")
        elif tags == ["nipt", "multiqc-html"]:
            return create_autospec(File, path="multiqc/file")
        elif tags == ["nipt", "wisecondor"]:
            return create_autospec(File, path="segmental_calls/file")
        raise NotImplementedError

    housekeeper_api.get_file_from_latest_version = mock_get_file
    mocker.patch.object(Path, "exists", return_value=True)
    nipt_upload_api.housekeeper_api = housekeeper_api

    # WHEN getting the statina files
    statina_files = nipt_upload_api.get_statina_files("case_id")

    # THEN the response looks as expected
    root_dir = nipt_upload_api_context.housekeeper.root
    expected_response = StatinaUploadFiles(
        data_set="novaseqx_data_set",
        result_file=f"{root_dir}/results/file",
        multiqc_report=f"{root_dir}/multiqc/file",
        segmental_calls=f"{root_dir}/segmental_calls",
    )
    assert statina_files == expected_response

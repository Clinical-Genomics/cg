"""Test module cg.cli.upload.nipt.statina"""

import logging

from click.testing import CliRunner

from cg.cli.upload.nipt.statina import batch
from cg.meta.upload.nipt import NiptUploadAPI
from cg.models.cg_config import CGConfig


class MockStatinaUploadFiles:
    def json(self, *args, **kwargs):
        return ""


def test_nipt_statina_upload_case(upload_context: CGConfig, cli_runner: CliRunner, caplog, mocker):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN a specified NIPT case
    case_id = "angrybird"

    # WHEN adding a result file of a specified NIPT case
    mocker.patch.object(NiptUploadAPI, "get_statina_files", return_value=MockStatinaUploadFiles())
    mocker.patch.object(NiptUploadAPI, "upload_to_statina_database")
    mocker.patch.object(NiptUploadAPI, "sequencing_run_passed_qc_value", return_value=True)
    result = cli_runner.invoke(batch, [case_id], obj=upload_context)

    # THEN the nipt upload should start and exit without errors
    assert "*** Statina UPLOAD START ***" in caplog.text
    assert result.exit_code == 0


def test_nipt_statina_upload_case_dry(
    upload_context: CGConfig, cli_runner: CliRunner, caplog, mocker
):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN a specified NIPT case
    case_id = "angrybird"

    # WHEN adding a result file of a specified NIPT case (dry run)
    mocker.patch.object(NiptUploadAPI, "get_statina_files", return_value=MockStatinaUploadFiles())
    mocker.patch.object(NiptUploadAPI, "upload_to_statina_database")
    result = cli_runner.invoke(batch, ["--dry-run", case_id], obj=upload_context)

    # THEN the nipt upload should start and exit without errors
    assert "*** Statina UPLOAD START ***" in caplog.text
    assert result.exit_code == 0

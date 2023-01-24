"""Test the Gens upload command"""

import logging

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.upload.gens import gens as upload_gens_cmd
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner


def test_upload_gens(
    upload_context: CGConfig,
    case_id: str,
    cli_runner: CliRunner,
    analysis_store_trio: Store,
    upload_genotypes_hk_api: HousekeeperAPI,
    caplog,
):
    """Test for Gens upload via the CLI"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a case that is ready for Gens upload
    upload_context.status_db_ = analysis_store_trio
    upload_context.housekeeper_api_ = upload_genotypes_hk_api
    case_obj = upload_context.status_db.family(case_id)
    assert case_obj

    # WHEN uploading to Gens
    result = cli_runner.invoke(upload_gens_cmd, ["--case-id", case_id], obj=upload_context)

    # THEN check that the command exits with success
    assert result.exit_code == 0

    # THEN assert the correct information is communicated
    assert "loading VCF genotypes for sample(s):" in caplog.text

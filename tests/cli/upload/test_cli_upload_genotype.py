"""Test the upload genotype command"""

import logging

from click.testing import CliRunner

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.upload.genotype import genotypes as upload_genotypes_cmd
from cg.store import Store


def test_upload_genotype(
    upload_context: dict,
    case_id: str,
    cli_runner: CliRunner,
    caplog,
    analysis_store_trio: Store,
    upload_genotypes_hk_api: HousekeeperAPI,
):
    """Test to upload genotypes via the CLI"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a case that is ready for upload sequence genotypes
    analysis_api = upload_context["analysis_api"]
    analysis_api.status_db = analysis_store_trio
    analysis_api.housekeeper_api = upload_genotypes_hk_api
    case_obj = upload_context["analysis_api"].status_db.family(case_id)
    assert case_obj

    # WHEN uploading the genotypes
    result = cli_runner.invoke(upload_genotypes_cmd, [case_id], obj=upload_context)
    # THEN check that the command exits with success
    assert result.exit_code == 0
    # THEN assert the correct information is communicated
    assert "loading VCF genotypes for sample(s):" in caplog.text

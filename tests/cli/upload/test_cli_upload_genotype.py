"""Test the upload genotype command"""

import logging

from click.testing import CliRunner

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.upload.genotype import upload_genotypes
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis
from cg.store.store import Store

LOG = logging.getLogger(__name__)

def test_upload_genotype_mip(
    upload_context_mip: CGConfig,
    case_id: str,
    cli_runner: CliRunner,
    analysis_store_trio: Store,
    upload_genotypes_hk_api_mip: HousekeeperAPI,
    caplog,
):
    """Test to upload genotypes via the CLI"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a case that is ready for upload sequence genotypes
    upload_context_mip.status_db_ = analysis_store_trio
    upload_context_mip.housekeeper_api_ = upload_genotypes_hk_api_mip
    case = upload_context_mip.status_db.get_case_by_internal_id(internal_id=case_id)
    assert case

    # WHEN uploading the genotypes
    result = cli_runner.invoke(upload_genotypes, [case_id], obj=upload_context_mip)

    # THEN check that the command exits with success
    assert result.exit_code == 0

    # THEN assert the correct information is communicated
    assert "loading VCF genotypes for sample(s):" in caplog.text


def test_upload_genotype_raredisease(
    upload_context_raredisease: CGConfig,
    raredisease_case_id: str,
    cli_runner: CliRunner,
    analysis_store_trio: Store,
    upload_genotypes_hk_api_raredisease: HousekeeperAPI,
    caplog,
):
    """Test to upload genotypes via the CLI"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a case that is ready for upload sequence genotypes
    upload_context_raredisease.status_db_ = analysis_store_trio
    upload_context_raredisease.housekeeper_api_ = upload_genotypes_hk_api_raredisease
    case = upload_context_raredisease.status_db.get_case_by_internal_id(internal_id=raredisease_case_id)
    LOG.info("been there")
    assert case

    # WHEN uploading the genotypes
    result = cli_runner.invoke(upload_genotypes, [raredisease_case_id], obj=upload_context_raredisease)

    # THEN check that the command exits with success
    assert result.exit_code == 0

    # THEN assert the correct information is communicated
    assert "loading VCF genotypes for sample(s):" in caplog.text

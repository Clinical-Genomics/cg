"""Test the upload genotype command"""

import logging
import pytest

from click.testing import CliRunner

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.cli.upload.genotype import upload_genotypes
from cg.models.cg_config import CGConfig
from cg.store.store import Store

LOG = logging.getLogger(__name__)

UPLOAD_CONTEXT = [
    ("balsamic"),
    ("mip"),
    ("raredisease")
]

@pytest.mark.parametrize(
    "upload_context",
    UPLOAD_CONTEXT,
    indirect=["upload_context"]
)
def test_upload_genotype(
    upload_context: CGConfig,
    mip_case_id: str,
    cli_runner: CliRunner,
    analysis_store_trio: Store,
    upload_genotypes_hk_api_mip: HousekeeperAPI,
    caplog,
):
    """Test to upload genotypes via the CLI"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a case that is ready for upload sequence genotypes
    upload_context.status_db_ = analysis_store_trio
    upload_context.housekeeper_api_ = upload_genotypes_hk_api_mip
    case = upload_context.status_db.get_case_by_internal_id(internal_id=mip_case_id)
    assert case

    # WHEN uploading the genotypes
    result = cli_runner.invoke(upload_genotypes, [mip_case_id], obj=upload_context)

    # THEN check that the command exits with success
    assert result.exit_code == 0

    # THEN assert the correct information is communicated
    assert "loading VCF genotypes for sample(s):" in caplog.text


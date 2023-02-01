"""Test the Gens upload command."""

import logging
from click.testing import CliRunner

from typing import Dict
from datetime import datetime, timedelta

from cg.constants import EXIT_SUCCESS
from cg.constants.sequencing import SequencingMethod
from cg.constants.subject import PhenotypeStatus
from cg.apps.gens import GensAPI
from cg.cli.upload.gens import gens as upload_gens_cmd
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Family, Sample
from cgmodels.cg.constants import Pipeline
from tests.store_helpers import StoreHelpers

def test_upload_gens(
    caplog,
    case_id: str,
    cli_runner: CliRunner,
    gens_config: Dict[str, Dict[str, str]],
    helpers: StoreHelpers,
    upload_context: CGConfig,
):
    """Test for Gens upload via the CLI."""
    caplog.set_level(logging.DEBUG)
    store: Store = upload_context.status_db
    upload_context.gens_api_ = GensAPI(gens_config)

    # GIVEN a case ready to be uploaded to Gens
    case: Family = helpers.add_case(store=store, internal_id=case_id)
    sample: Sample = helpers.add_sample(store=store, application_type=SequencingMethod.WGS)
    store.relate_sample(family=case, sample=sample, status=PhenotypeStatus.UNKNOWN)

    # GIVEN an analysis ready to be uploaded to Gens
    completed_at: datetime = datetime.now()
    started_at = completed_at - timedelta(hours=100)
    helpers.add_analysis(store=store, case=case, pipeline=Pipeline.MIP_DNA, started_at=started_at, completed_at=completed_at)

    # WHEN uploading to Gens
    result = cli_runner.invoke(upload_gens_cmd, [case_id, "--dry-run"], obj=upload_context)

    # THEN check that the command exits with success
    assert result.exit_code == EXIT_SUCCESS

    # THEN assert the correct information is communicated

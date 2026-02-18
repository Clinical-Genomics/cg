"""Test the Gens upload command."""

import logging
from unittest.mock import Mock, create_autospec

from click.testing import CliRunner

from cg.apps.gens import GensAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.upload.gens import upload_to_gens as upload_gens_cmd
from cg.constants import EXIT_SUCCESS, Workflow
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_upload_gens(
    caplog,
    case_id: str,
    cli_runner: CliRunner,
    upload_gens_context: CGConfig,
):
    """Test for Gens upload via the CLI."""
    caplog.set_level(logging.DEBUG)

    # WHEN uploading to Gens
    result = cli_runner.invoke(upload_gens_cmd, [case_id, "--dry-run"], obj=upload_gens_context)

    # THEN check that the command exits with success
    assert result.exit_code == EXIT_SUCCESS
    assert "Dry run" in caplog.text


def test_upload_gens_genome_build_38(cli_runner: CliRunner, upload_gens_context: CGConfig):
    # GIVEN a Raredisease case
    status_db: Store = create_autospec(Store)
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, data_analysis=Workflow.RAREDISEASE, samples=[sample])
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)
    upload_gens_context.status_db_ = status_db

    gens_api: TypedMock[GensAPI] = create_typed_mock(GensAPI)
    upload_gens_context.gens_api_ = gens_api.as_type

    # GIVEN a HousekeeperAPI
    housekeeper_api = create_autospec(HousekeeperAPI)

    # WHEN uploading to Gens
    result = cli_runner.invoke(upload_gens_cmd, ["some_case"], obj=upload_gens_context)

    # THEN assert gens is called with correct genome build
    gens_api.as_mock.load.assert_called_once_with()

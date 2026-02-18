"""Test the Gens upload command."""

import logging
from unittest.mock import Mock, create_autospec

from click.testing import CliRunner
from housekeeper.store.models import File

from cg.apps.gens import GensAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.upload.gens import upload_to_gens as upload_gens_cmd
from cg.constants import EXIT_SUCCESS, Workflow
from cg.constants.constants import GenomeBuild
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
    # GIVEN a store
    status_db: Store = create_autospec(Store)

    # GIVEN a Raredisease case with a sample
    sample: Sample = create_autospec(Sample, internal_id="sample_id")
    case: Case = create_autospec(Case, data_analysis=Workflow.RAREDISEASE, samples=[sample])

    status_db.get_case_by_internal_id_strict = Mock(return_value=case)
    upload_gens_context.status_db_ = status_db
    gens_api: TypedMock[GensAPI] = create_typed_mock(GensAPI)
    upload_gens_context.gens_api_ = gens_api.as_type

    # GIVEN a HousekeeperAPI
    file_path = "/path/to/file"
    housekeeper_api = create_autospec(HousekeeperAPI)
    housekeeper_api.get_file_from_latest_version = Mock(
        return_value=create_autospec(File, full_path=file_path)
    )
    upload_gens_context.housekeeper_api_ = housekeeper_api

    # WHEN uploading to Gens
    cli_runner.invoke(upload_gens_cmd, ["some_case"], obj=upload_gens_context)

    # THEN assert gens is called with correct genome build
    gens_api.as_mock.load.assert_called_once_with(
        baf_path=file_path,
        case_id="some_case",
        coverage_path=file_path,
        genome_build=GenomeBuild.hg38,
        sample_id="sample_id",
    )

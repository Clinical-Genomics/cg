import logging
import mock
from click.testing import CliRunner, Result

from cg.constants import Pipeline, EXIT_SUCCESS
from cg.cli.upload.scout import create_scout_load_config
from cg.models.cg_config import CGConfig
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.meta.upload.balsamic.balsamic import BalsamicUploadAPI
from cg.store import Store
from cg.store.models import Family

from tests.store_helpers import StoreHelpers
from tests.mocks.scout import MockScoutLoadConfig


def test_create_scout_load_config(
    caplog,
    cli_runner: CliRunner,
    cg_context: CGConfig,
    case_id: str,
    helpers: StoreHelpers,
):
    """Test to create a scout load config for a BALSAMIC case."""
    caplog.set_level(logging.DEBUG)
    status_db: Store = cg_context.status_db

    # GIVEN a case with a balsamic analysis
    case: Family = helpers.ensure_case(
        store=status_db, data_analysis=Pipeline.BALSAMIC, case_id=case_id
    )
    helpers.add_analysis(store=status_db, pipeline=Pipeline.BALSAMIC, case=case)

    with mock.patch.object(UploadScoutAPI, "generate_config", return_value=MockScoutLoadConfig()):
        # WHEN creating the scout load config
        result: Result = cli_runner.invoke(
            create_scout_load_config, ["--print", case_id], obj=cg_context
        )

        # THEN assert that the type of upload API is correct
        assert type(cg_context.meta_apis["upload_api"]) == BalsamicUploadAPI
        # THEN assert that the code exits with success
        assert result.exit_code == EXIT_SUCCESS
        # THEN assert that the root path is in the log
        assert cg_context.meta_apis["upload_api"].analysis_api.root in caplog.text

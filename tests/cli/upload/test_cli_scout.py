import logging

from click.testing import CliRunner

from cg.constants import Pipeline
from cg.cli.upload.scout import create_scout_load_config
from cg.models.cg_config import CGConfig
from cg.meta.upload.balsamic.balsamic import BalsamicUploadAPI
from cg.store import Store
from cg.store.models import Family

from tests.store_helpers import StoreHelpers
from tests.cli.upload.conftest import MockScoutUploadApi


def test_create_scout_load_config(
    caplog,
    cli_runner: CliRunner,
    cg_context: CGConfig,
    case_id: str,
    helpers: StoreHelpers,
    upload_scout_api: MockScoutUploadApi,
):
    """Test to create a scout load config for a BALSAMIC case"""
    caplog.set_level(logging.DEBUG)
    status_db: Store = cg_context.status_db
    cg_context.meta_apis["upload_api"] = BalsamicUploadAPI(cg_context)
    cg_context.meta_apis["upload_api"].scout_upload_api = upload_scout_api
    # GIVEN a case with a balsamic analysis
    case: Family = helpers.ensure_case(
        store=status_db, data_analysis=Pipeline.BALSAMIC, case_id=case_id
    )
    helpers.add_analysis(store=status_db, pipeline=Pipeline.BALSAMIC, case=case)
    # GIVEN a BalsamicUploadAPI with an AnalysisAPI with a root
    upload_api: BalsamicUploadAPI = BalsamicUploadAPI(cg_context)
    # WHEN creating the scout load config
    result = cli_runner.invoke(create_scout_load_config, ["--print", case_id], obj=cg_context)
    # THEN assert that the correct root is set
    assert result.exit_code == 0
    assert upload_api.analysis_api.root in caplog.text

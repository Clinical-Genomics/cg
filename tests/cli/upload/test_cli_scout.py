import logging

import mock
import pytest
from click.testing import CliRunner, Result

from cg.cli.upload.scout import create_scout_load_config, get_upload_api
from cg.constants import EXIT_SUCCESS, Workflow
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.meta.workflow.tomte import TomteAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from cg.store.store import Store
from tests.mocks.scout import MockScoutLoadConfig
from tests.store_helpers import StoreHelpers

WORKFLOWS_TO_TEST: list = [
    Workflow.BALSAMIC,
    Workflow.MIP_DNA,
    Workflow.MIP_RNA,
    Workflow.RNAFUSION,
]

ANALYSIS_API: list = [
    (Workflow.BALSAMIC, BalsamicAnalysisAPI),
    (Workflow.MIP_DNA, MipDNAAnalysisAPI),
    (Workflow.MIP_RNA, MipRNAAnalysisAPI),
    (Workflow.RNAFUSION, RnafusionAnalysisAPI),
    (Workflow.TOMTE, TomteAnalysisAPI),
]


@pytest.mark.parametrize(
    "workflow,analysis_api",
    ANALYSIS_API,
)
def test_get_upload_api(
    cg_context: CGConfig,
    case_id: str,
    helpers: StoreHelpers,
    workflow: Workflow,
    analysis_api: AnalysisAPI,
):
    """Test to get the correct upload API for a case."""
    status_db: Store = cg_context.status_db

    # GIVEN a case with a balsamic analysis
    case: Case = helpers.ensure_case(store=status_db, data_analysis=workflow, case_id=case_id)
    helpers.add_analysis(store=status_db, case=case, workflow=workflow)

    # WHEN getting the upload API
    upload_api: UploadAPI = get_upload_api(cg_config=cg_context, case=case)

    # THEN assert that the type of upload API is correct
    assert isinstance(upload_api.analysis_api, analysis_api)


@pytest.mark.parametrize(
    "workflow",
    WORKFLOWS_TO_TEST,
)
def test_create_scout_load_config(
    caplog,
    cli_runner: CliRunner,
    cg_context: CGConfig,
    case_id: str,
    helpers: StoreHelpers,
    workflow: Workflow,
):
    """Test to create a scout load config for a case."""
    caplog.set_level(logging.DEBUG)
    status_db: Store = cg_context.status_db

    # GIVEN a case with a balsamic analysis
    case: Case = helpers.ensure_case(store=status_db, data_analysis=workflow, case_id=case_id)
    helpers.add_analysis(store=status_db, case=case, workflow=workflow)

    with mock.patch.object(UploadScoutAPI, "generate_config", return_value=MockScoutLoadConfig()):
        # WHEN creating the scout load config
        result: Result = cli_runner.invoke(
            create_scout_load_config, ["--print", case_id], obj=cg_context
        )

        # THEN assert that the code exits with success
        assert result.exit_code == EXIT_SUCCESS
        # THEN assert that the root path is in the log
        assert cg_context.meta_apis["upload_api"].analysis_api.root in caplog.text

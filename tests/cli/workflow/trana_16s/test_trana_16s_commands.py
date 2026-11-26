from unittest.mock import Mock, create_autospec

from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.apps.tb.api import TrailblazerAPI
from cg.cli.workflow.trana_16s.trana_16s_commands import analysis_qc_service, perform_qc_check
from cg.models.cg_config import CGConfig, TranaConfig
from cg.store.models import Analysis, Case
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_perform_qc_check(mocker: MockerFixture):
    # GIVEN a case with an analysis
    case: Case = create_autospec(Case)
    case.get_latest_analysis_strict = Mock(return_value=create_autospec(Analysis, id=2))

    # GIVEN a StatusDB
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(
        CGConfig,
        trana_16s=create_autospec(TranaConfig, root="root_dir"),
        status_db=status_db.as_type,
        trailblazer_api=create_autospec(TrailblazerAPI),
    )

    # GIVEN an analysis QC service
    perform_qc_mock = mocker.patch.object(analysis_qc_service, "perform_qc")

    # WHEN calling perform_qc_check
    cli_runner = CliRunner()
    cli_runner.invoke(perform_qc_check, ["case_id"], obj=cg_config)

    # THEN we should have fetched the case using the provided case id
    status_db.as_mock.get_case_by_internal_id_strict.assert_called_once_with("case_id")

    # THEN perform_qc was called with the correct parameters
    perform_qc_mock.assert_called_once_with(
        root_directory="root_dir",
        status_db=cg_config.status_db,
        trailblazer_api=cg_config.trailblazer_api,
        analysis_id=2,
    )

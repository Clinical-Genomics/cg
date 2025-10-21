from unittest.mock import ANY, Mock, create_autospec

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.workflow.balsamic.base import dev_start
from cg.constants import Workflow
from cg.models.cg_config import BalsamicConfig, CGConfig, IlluminaConfig, RunInstruments
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.service import AnalysisStarter


@pytest.fixture
def cg_config(cg_balsamic_config: BalsamicConfig) -> CGConfig:
    return create_autospec(
        CGConfig,
        balsamic=cg_balsamic_config,
        data_flow=Mock(),
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
    )


def test_balsamic_start_all_flags(
    cg_config: CGConfig,
    mocker: MockerFixture,
):
    # GIVEN a cli runner
    cli_runner = CliRunner()

    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a CGConfig with configuration info for Balsamic

    # GIVEN the analysis starter factory can create an analysis starter
    get_analysis_starter_spy = mocker.spy(
        AnalysisStarterFactory, "get_analysis_starter_for_workflow"
    )

    # GIVEN that the analysis starter can start the case
    mock_start = mocker.patch.object(AnalysisStarter, "start")

    # GIVEN all possible flags
    panel_bed = "panel.bed"
    workflow_profile = "profile"
    flags: list[str] = [
        "--panel-bed",
        panel_bed,
        "--workflow-profile",
        workflow_profile,
        case_id,
    ]

    # WHEN invoking cg workflow Balsamic dev-start
    result = cli_runner.invoke(dev_start, flags, obj=cg_config, catch_exceptions=False)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis starter should have been created and called
    get_analysis_starter_spy.assert_called_once_with(ANY, Workflow.BALSAMIC)
    mock_start.assert_called_once_with(
        case_id=case_id,
        panel_bed=panel_bed,
        workflow_profile=workflow_profile,
    )

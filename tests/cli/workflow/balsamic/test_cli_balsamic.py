from pathlib import Path
from unittest.mock import ANY, MagicMock, Mock, create_autospec

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.workflow.balsamic.base import dev_config_case, dev_run, dev_start
from cg.constants import Workflow
from cg.models.cg_config import BalsamicConfig, CGConfig, IlluminaConfig, RunInstruments
from cg.services.analysis_starter.configurator.implementations.balsamic import BalsamicConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.service import AnalysisStarter


@pytest.fixture
def cg_config_for_balsamic_cli(cg_balsamic_config: BalsamicConfig) -> CGConfig:
    return create_autospec(
        CGConfig,
        balsamic=cg_balsamic_config,
        data_flow=Mock(),
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
    )


def test_balsamic_config_case_all_flags(
    cg_config_for_balsamic_cli: CGConfig, mocker: MockerFixture
):
    # GIVEN a CLIRunner
    cli_runner = CliRunner()

    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a CGConfig with configuration info for Balsamic

    # GIVEN the configurator factory can create a configurator
    get_configurator_spy = mocker.spy(ConfiguratorFactory, "get_configurator")

    # GIVEN that the configurator can configure the case
    mock_configure = mocker.patch.object(BalsamicConfigurator, "configure")

    # WHEN invoking cg workflow mip-dna dev-case-config
    result = cli_runner.invoke(
        dev_config_case,
        ["--panel-bed", "panel_short_name", case_id],
        obj=cg_config_for_balsamic_cli,
    )

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the configurator should have been created and called
    get_configurator_spy.assert_called_once_with(ANY, Workflow.BALSAMIC)
    mock_configure.assert_called_once_with(case_id=case_id, panel_bed="panel_short_name")


def test_mip_dna_config_case_no_flags(cg_config_for_balsamic_cli: CGConfig, mocker: MockerFixture):
    # GIVEN a CLIRunner
    cli_runner = CliRunner()

    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a CGConfig with configuration info for Balsamic

    # GIVEN the configurator factory can create a configurator
    get_configurator_spy = mocker.spy(ConfiguratorFactory, "get_configurator")

    # GIVEN that the configurator can configure the case
    mock_configure = mocker.patch.object(BalsamicConfigurator, "configure")

    # WHEN invoking cg workflow mip-dna dev-case-config
    result = cli_runner.invoke(dev_config_case, [case_id], obj=cg_config_for_balsamic_cli)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the configurator should have been created and called
    get_configurator_spy.assert_called_once_with(ANY, Workflow.BALSAMIC)
    mock_configure.assert_called_once_with(case_id=case_id, panel_bed=None)


def test_balsamic_run_all_flags(
    cg_config_for_balsamic_cli: CGConfig, tmp_path: Path, mocker: MockerFixture
):
    # GIVEN a CLI runner
    cli_runner = CliRunner()

    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a CGConfig with configuration info for Balsamic

    # GIVEN the analysis starter factory can create an analysis starter
    get_analysis_starter_spy = mocker.spy(
        AnalysisStarterFactory, "get_analysis_starter_for_workflow"
    )

    # GIVEN that the analysis starter can run the case
    mock_run = mocker.patch.object(AnalysisStarter, "run")

    # GIVEN all possible flags
    workflow_profile = tmp_path
    flags: list[str] = ["--workflow-profile", workflow_profile, case_id]

    # WHEN invoking cg workflow mip-dna dev-run
    result = cli_runner.invoke(
        dev_run, flags, obj=cg_config_for_balsamic_cli, catch_exceptions=False
    )

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis starter should have been created and called
    get_analysis_starter_spy.assert_called_once_with(ANY, Workflow.BALSAMIC)
    mock_run.assert_called_once_with(case_id=case_id, workflow_profile=workflow_profile)


def test_balsamic_run_no_flags(cg_config_for_balsamic_cli: CGConfig, mocker: MockerFixture):
    # GIVEN a CLI runner
    cli_runner = CliRunner()

    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a CGConfig with configuration info for Balsamic

    # GIVEN the analysis starter factory can create an analysis starter
    get_analysis_starter_spy = mocker.spy(
        AnalysisStarterFactory, "get_analysis_starter_for_workflow"
    )

    # GIVEN that the analysis starter can run the case
    mock_run: MagicMock = mocker.patch.object(AnalysisStarter, "run")

    # GIVEN no flags
    flags: list[str] = [case_id]

    # WHEN invoking cg workflow mip-dna dev-run
    result = cli_runner.invoke(
        dev_run, flags, obj=cg_config_for_balsamic_cli, catch_exceptions=False
    )

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis starter should have been created and called
    get_analysis_starter_spy.assert_called_once_with(ANY, Workflow.BALSAMIC)
    mock_run.assert_called_once_with(case_id=case_id, workflow_profile=None)


def test_balsamic_start_all_flags(
    cg_config_for_balsamic_cli: CGConfig,
    mocker: MockerFixture,
    tmp_path: Path,
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
    workflow_profile = tmp_path
    flags: list[str] = [
        "--panel-bed",
        panel_bed,
        "--workflow-profile",
        workflow_profile,
        case_id,
    ]

    # WHEN invoking cg workflow Balsamic dev-start
    result = cli_runner.invoke(
        dev_start, flags, obj=cg_config_for_balsamic_cli, catch_exceptions=False
    )

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis starter should have been created and called with the flag values
    get_analysis_starter_spy.assert_called_once_with(ANY, Workflow.BALSAMIC)
    mock_start.assert_called_once_with(
        case_id=case_id,
        panel_bed=panel_bed,
        workflow_profile=workflow_profile,
    )


def test_balsamic_start_no_flags(cg_config_for_balsamic_cli: CGConfig, mocker: MockerFixture):
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

    # GIVEN no cli flags
    flags: list[str] = [case_id]

    # WHEN invoking cg workflow mip-dna dev-start
    result = cli_runner.invoke(
        dev_start, flags, obj=cg_config_for_balsamic_cli, catch_exceptions=False
    )

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis starter should have been created and called
    get_analysis_starter_spy.assert_called_once_with(ANY, Workflow.BALSAMIC)
    mock_start.assert_called_once_with(case_id=case_id, panel_bed=None, workflow_profile=None)

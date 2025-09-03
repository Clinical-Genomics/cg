from unittest.mock import ANY, Mock, create_autospec

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.workflow.mip_dna.base import dev_config_case, dev_run, dev_start
from cg.constants import Workflow
from cg.models.cg_config import CGConfig, IlluminaConfig, MipConfig, RunInstruments
from cg.services.analysis_starter.configurator.implementations.mip_dna import MIPDNAConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.service import AnalysisStarter


@pytest.fixture
def cg_config() -> CGConfig:
    mip_rd_dna_config: MipConfig = create_autospec(
        MipConfig,
        root="root",
        conda_binary="conda/binary",
        conda_env="conda_env",
        mip_config="mip/config.config",
        workflow=Workflow.MIP_DNA,
        script="script",
    )
    return create_autospec(
        CGConfig,
        mip_rd_dna=mip_rd_dna_config,
        data_flow=Mock(),
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
    )


def test_mip_dna_dev_run_no_flags(cg_config: CGConfig, mocker: MockerFixture):
    # GIVEN a CLI runner
    cli_runner = CliRunner()

    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a CGConfig with configuration info for MIP-DNA

    # GIVEN the analysis starter factory can create an analysis starter
    get_analysis_starter_spy = mocker.spy(
        AnalysisStarterFactory, "get_analysis_starter_for_workflow"
    )

    # GIVEN that the analysis starter can run the case
    mock_run = mocker.patch.object(AnalysisStarter, "run")

    # GIVEN no flags
    flags: list[str] = [case_id]

    # WHEN invoking cg workflow mip-dna dev-run
    result = cli_runner.invoke(dev_run, flags, obj=cg_config)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis starter should have been created and called
    get_analysis_starter_spy.assert_called_once_with(ANY, Workflow.MIP_DNA)
    mock_run.assert_called_once_with(
        case_id=case_id, start_after=None, start_with=None, use_bwa_mem=False
    )


def test_mip_dna_dev_run_all_flags(cg_config: CGConfig, mocker: MockerFixture):
    # GIVEN a CLI runner
    cli_runner = CliRunner()

    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a CGConfig with configuration info for MIP-DNA

    # GIVEN the analysis starter factory can create an analysis starter
    get_analysis_starter_spy = mocker.spy(
        AnalysisStarterFactory, "get_analysis_starter_for_workflow"
    )

    # GIVEN that the analysis starter can run the case
    mock_run = mocker.patch.object(AnalysisStarter, "run")

    # GIVEN all possible flags
    start_after = "levain_bread"
    start_with = "dinkel_bread"
    flags = ["--start-with", start_with, "--start-after", start_after, "--use-bwa-mem", case_id]

    # WHEN invoking cg workflow mip-dna dev-run
    result = cli_runner.invoke(dev_run, flags, obj=cg_config)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis starter should have been created and called
    get_analysis_starter_spy.assert_called_once_with(ANY, Workflow.MIP_DNA)
    mock_run.assert_called_once_with(
        case_id=case_id, start_after=start_after, start_with=start_with, use_bwa_mem=True
    )


def test_mip_dna_dev_start_no_flags(
    cg_config: CGConfig,
    mocker: MockerFixture,
):
    # GIVEN a cli runner
    cli_runner = CliRunner()

    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a CGConfig with configuration info for MIP-DNA

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
        dev_start,
        flags,
        obj=cg_config,
    )

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis starter should have been created and called
    get_analysis_starter_spy.assert_called_once_with(ANY, Workflow.MIP_DNA)
    mock_start.assert_called_once_with(
        case_id=case_id,
        panel_bed=None,
        start_after=None,
        use_bwa_mem=False,
        start_with=None,
    )


def test_mip_dna_dev_start_all_flags(
    cg_config: CGConfig,
    mocker: MockerFixture,
):
    # GIVEN a cli runner
    cli_runner = CliRunner()

    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a CGConfig with configuration info for MIP-DNA

    # GIVEN the analysis starter factory can create an analysis starter
    get_analysis_starter_spy = mocker.spy(
        AnalysisStarterFactory, "get_analysis_starter_for_workflow"
    )

    # GIVEN that the analysis starter can start the case
    mock_start = mocker.patch.object(AnalysisStarter, "start")

    # GIVEN all possible flags
    panel_bed = "panel.bed"
    start_after = "levain_bread"
    start_with = "dinkel_bread"
    flags: list[str] = [
        "--panel-bed",
        panel_bed,
        "--start-with",
        start_with,
        "--start-after",
        start_after,
        "--use-bwa-mem",
        case_id,
    ]

    # WHEN invoking cg workflow mip-dna dev-start
    result = cli_runner.invoke(
        dev_start,
        flags,
        obj=cg_config,
    )

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis starter should have been created and called
    get_analysis_starter_spy.assert_called_once_with(ANY, Workflow.MIP_DNA)
    mock_start.assert_called_once_with(
        case_id=case_id,
        panel_bed=panel_bed,
        start_after=start_after,
        use_bwa_mem=True,
        start_with=start_with,
    )


def test_mip_dna_dev_config_case_all_flags(cg_config: CGConfig, mocker: MockerFixture):
    # GIVEN a CLIRunner
    cli_runner = CliRunner()

    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a CGConfig with configuration info for MIP-DNA

    # GIVEN the configurator factory can create a configurator
    get_configurator_spy = mocker.spy(ConfiguratorFactory, "get_configurator")

    # GIVEN that the configurator can configure the case
    mock_configure = mocker.patch.object(MIPDNAConfigurator, "configure")

    # WHEN invoking cg workflow mip-dna dev-case-config
    result = cli_runner.invoke(
        dev_config_case, ["--panel-bed", "panel.bed", case_id], obj=cg_config
    )

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the configurator should have been created and called
    get_configurator_spy.assert_called_once_with(ANY, Workflow.MIP_DNA)
    mock_configure.assert_called_once_with(case_id=case_id, panel_bed="panel.bed")


def test_mip_dna_dev_config_case_no_flags(cg_config: CGConfig, mocker: MockerFixture):
    # GIVEN a CLIRunner
    cli_runner = CliRunner()

    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a CGConfig with configuration info for MIP-DNA

    # GIVEN the configurator factory can create a configurator
    get_configurator_spy = mocker.spy(ConfiguratorFactory, "get_configurator")

    # GIVEN that the configurator can configure the case
    mock_configure = mocker.patch.object(MIPDNAConfigurator, "configure")

    # WHEN invoking cg workflow mip-dna dev-case-config
    result = cli_runner.invoke(dev_config_case, [case_id], obj=cg_config)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the configurator should have been created and called
    get_configurator_spy.assert_called_once_with(ANY, Workflow.MIP_DNA)
    mock_configure.assert_called_once_with(case_id=case_id, panel_bed=None)

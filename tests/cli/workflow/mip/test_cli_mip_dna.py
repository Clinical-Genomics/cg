from unittest.mock import ANY, Mock, create_autospec

from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.workflow.mip_dna.base import dev_run
from cg.constants import Workflow
from cg.models.cg_config import CGConfig, IlluminaConfig, MipConfig, RunInstruments
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.service import AnalysisStarter


def test_mip_dna_dev_run(mocker: MockerFixture):
    # GIVEN a CLI runner
    cli_runner = CliRunner()

    # GIVEN a CG Config with a MIP-DNA config
    mip_rd_dna_config: MipConfig = create_autospec(
        MipConfig,
        root="root",
        conda_binary="conda/binary",
        conda_env="conda_env",
        mip_config="mip/config.config",
        workflow=Workflow.MIP_DNA,
        script="script",
    )
    cg_config: CGConfig = create_autospec(
        CGConfig,
        mip_rd_dna=mip_rd_dna_config,
        data_flow=Mock(),
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
    )

    get_analysis_starter_spy = mocker.spy(
        AnalysisStarterFactory, "get_analysis_starter_for_workflow"
    )
    mock_run = mocker.patch.object(AnalysisStarter, "run")

    # WHEN invoking cg workflow mip-dna dev-run
    result = cli_runner.invoke(dev_run, ["case_id"], obj=cg_config)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis starter should have been called
    get_analysis_starter_spy.assert_called_once_with(ANY, Workflow.MIP_DNA)
    mock_run.assert_called_once_with("case_id")

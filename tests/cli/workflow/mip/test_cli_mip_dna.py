from unittest.mock import ANY, Mock, create_autospec

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.workflow.mip_dna.base import dev_run, dev_start
from cg.constants import Workflow
from cg.models.cg_config import CGConfig, IlluminaConfig, MipConfig, RunInstruments
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


@pytest.mark.parametrize(
    "cli_args, start_after, start_with, use_bwa_mem",
    [
        (["case_id"], None, None, False),
        (
            [
                "--start-with",
                "dinkel_bread",
                "--start-after",
                "levain_bread",
                "--use-bwa-mem",
                "case_id",
            ],
            "levain_bread",
            "dinkel_bread",
            True,
        ),
    ],
    ids=["No arguments", "All arguments"],
)
def test_mip_dna_dev_run(
    cli_args: list[str],
    start_after: str | None,
    start_with: str | None,
    use_bwa_mem: bool,
    cg_config: CGConfig,
    mocker: MockerFixture,
):
    # GIVEN a CLI runner
    cli_runner = CliRunner()

    # GIVEN a CG Config with a MIP-DNA config

    get_analysis_starter_spy = mocker.spy(
        AnalysisStarterFactory, "get_analysis_starter_for_workflow"
    )
    mock_run = mocker.patch.object(AnalysisStarter, "run")

    # WHEN invoking cg workflow mip-dna dev-run
    result = cli_runner.invoke(dev_run, cli_args, obj=cg_config)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis starter should have been created and called
    get_analysis_starter_spy.assert_called_once_with(ANY, Workflow.MIP_DNA)
    mock_run.assert_called_once_with(
        case_id="case_id", start_after=start_after, start_with=start_with, use_bwa_mem=use_bwa_mem
    )


@pytest.mark.parametrize(
    "cli_args, panel_bed, start_after, start_with, use_bwa_mem",
    [
        (["case_id"], None, None, None, False),
        (
            [
                "--panel-bed",
                "panel.bed",
                "--start-with",
                "dinkel_bread",
                "--start-after",
                "levain_bread",
                "--use-bwa-mem",
                "case_id",
            ],
            "panel.bed",
            "levain_bread",
            "dinkel_bread",
            True,
        ),
    ],
    ids=["No arguments", "All arguments"],
)
def test_mip_dna_dev_start(
    cli_args: list[str],
    panel_bed: str | None,
    start_after: str | None,
    start_with: str | None,
    use_bwa_mem: bool,
    cg_config: CGConfig,
    mocker: MockerFixture,
):
    # GIVEN a cli runner
    cli_runner = CliRunner()

    # GIVEN a CGConfig with a MIP-DNA config

    get_analysis_starter_spy = mocker.spy(
        AnalysisStarterFactory, "get_analysis_starter_for_workflow"
    )
    mock_start = mocker.patch.object(AnalysisStarter, "start")

    # WHEN invoking cg workflow mip-dna dev-start
    result = cli_runner.invoke(
        dev_start,
        cli_args,
        obj=cg_config,
    )

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis starter should have been created and called
    get_analysis_starter_spy.assert_called_once_with(ANY, Workflow.MIP_DNA)
    mock_start.assert_called_once_with(
        case_id="case_id",
        panel_bed=panel_bed,
        start_after=start_after,
        use_bwa_mem=use_bwa_mem,
        start_with=start_with,
    )

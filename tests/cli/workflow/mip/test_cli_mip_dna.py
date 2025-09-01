from unittest.mock import Mock, create_autospec

from click.testing import CliRunner

from cg.constants import Workflow
from cg.models.cg_config import CGConfig, IlluminaConfig, MipConfig, RunInstruments


def test_mip_dna_dev_run():
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

    # WHEN invoking cg workflow mip-dna dev-run
    cli_runner.invoke(dev_run, ["case_id"], obj=cg_config)

    # THEN the analysis starter should have been called

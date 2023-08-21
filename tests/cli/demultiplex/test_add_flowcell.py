from pathlib import Path

from cg.cli.demultiplex.add import add_flow_cell_cmd
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from click.testing import CliRunner


def test_add_flowcell_cmd(
    cli_runner: CliRunner,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
    demultiplex_context: CGConfig,
    tmp_demultiplexed_runs_directory: Path,
    tmp_flow_cell_directory_bcl2fastq: Path,
):
    # GIVEN a cgstats api and a demultiplex api
    # GIVEN that there is a flow cell in the directory
    assert tmp_flow_cell_directory_bcl2fastq.exists()
    # GIVEN that there is a demultiplexed flow cell
    assert tmp_demultiplexed_runs_directory.exists()

    # GIVEN that the flowcell does not exist in the cgstats database
    assert not demultiplex_context.cg_stats_api.find_handler.get_flow_cell_by_name(
        flow_cell_name=bcl2fastq_flow_cell.id
    )

    # WHEN running the add flowcell command
    result = cli_runner.invoke(
        add_flow_cell_cmd,
        [bcl2fastq_flow_cell.full_name],
        obj=demultiplex_context,
    )

    # THEN assert that the run was success
    assert result.exit_code == 0
    # THEN assert that the flowcell was added to cgstats
    assert demultiplex_context.cg_stats_api.find_handler.get_flow_cell_by_name(
        flow_cell_name=bcl2fastq_flow_cell.id
    )

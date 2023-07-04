from pathlib import Path

from cg.cli.demultiplex.add import add_flow_cell_cmd
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from click.testing import CliRunner


def test_add_flowcell_cmd(
    cli_runner: CliRunner,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
    demultiplex_context: CGConfig,
    demultiplexed_flow_cell_finished_working_directory: Path,
    demultiplex_ready_flow_cell: Path,
):
    # GIVEN a cgstats api and a demultiplex api
    # GIVEN that there is a flowcell in the run dir
    assert demultiplex_ready_flow_cell.exists()
    # GIVEN that there is a demultiplexed flowcell
    assert demultiplexed_flow_cell_finished_working_directory.exists()

    # GIVEN that the flowcell does not exist in the cgstats database
    assert not demultiplex_context.cg_stats_api.find_handler.get_flow_cell_by_name(
        flow_cell_name=bcl2fastq_flow_cell.id
    )

    # WHEN running the add flowcell command
    result = cli_runner.invoke(
        add_flow_cell_cmd, [bcl2fastq_flow_cell.full_name], obj=demultiplex_context
    )

    # THEN assert that the run was success
    assert result.exit_code == 0
    # THEN assert that the flowcell was added to cgstats
    assert demultiplex_context.cg_stats_api.find_handler.get_flow_cell_by_name(
        flow_cell_name=bcl2fastq_flow_cell.id
    )

from pathlib import Path

from cg.apps.cgstats.crud.find import get_flowcell_id
from cg.cli.demultiplex.add import add_flowcell_cmd
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell
from click.testing import CliRunner


def test_add_flowcell_cmd(
    cli_runner: CliRunner,
    flowcell_object: Flowcell,
    demultiplex_context: CGConfig,
    demultiplexed_flowcell_finished_working_directory: Path,
    demultiplex_ready_flowcell: Path,
):
    # GIVEN a cgstats api and a demultiplex api
    # GIVEN that there is a flowcell in the run dir
    assert demultiplex_ready_flowcell.exists()
    # GIVEN that there is a demultiplexed flowcell
    assert demultiplexed_flowcell_finished_working_directory.exists()

    # GIVEN that the flowcell does not exist in the cgstats database
    assert not get_flowcell_id(flowcell_name=flowcell_object.flowcell_id)

    # WHEN running the add flowcell command
    result = cli_runner.invoke(
        add_flowcell_cmd, [flowcell_object.flowcell_full_name], obj=demultiplex_context
    )

    # THEN assert that the run was success
    assert result.exit_code == 0
    # THEN assert that the flowcell was added to cgstats
    assert get_flowcell_id(flowcell_name=flowcell_object.flowcell_id)

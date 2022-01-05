from pathlib import Path

from click.testing import CliRunner

from cg.apps.cgstats.crud import find
from cg.apps.cgstats.stats import StatsAPI
from cg.cli.demultiplex.add import select_project_cmd
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flowcell import Flowcell


def test_select_command(
    cli_runner: CliRunner,
    populated_stats_api: StatsAPI,
    demux_results_finished_dir: Path,
    flowcell_object: Flowcell,
    demultiplex_context: CGConfig,
):
    demultiplex_context.cg_stats_api_ = populated_stats_api
    # GIVEN a stats api with some information about a flowcell
    flowcell_id: str = flowcell_object.flowcell_id
    full_flowcell_name: str = flowcell_object.flowcell_full_name
    assert find.get_flowcell_id(flowcell_id)
    demux_results = DemuxResults(
        demux_dir=demux_results_finished_dir / full_flowcell_name,
        flowcell=flowcell_object,
        bcl_converter="bcl2fastq",
    )

    # GIVEN a project id
    project_id: str = ""
    for project in demux_results.projects:
        project_id = project.split("_")[-1]
    assert project_id

    # WHEN exporting the sample information
    result = cli_runner.invoke(
        select_project_cmd, [flowcell_id, "--project", project_id], obj=demultiplex_context
    )

    # THEN assert that the command exits with success
    assert result.exit_code == 0
    # THEN assert that the flowcell id if in the printing
    assert flowcell_id in result.output

from pathlib import Path

from cg.apps.cgstats.stats import StatsAPI
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flowcell import Flowcell


def test_rename_demux_result(
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
    caplog,
):

    # GIVEN that this is the location of the demultiplex api
    demultiplex_context.demultiplex_api_.out_dir = demultiplexed_flowcell_working_directory
    post_demux_api: DemuxPostProcessingAPI = DemuxPostProcessingAPI(config=demultiplex_context)
    demux_dir: Path = demultiplexed_flowcell_working_directory
    demux_results: DemuxResults = DemuxResults(demux_dir=demux_dir, flowcell=flowcell_object)
    # GIVEN that there are no projects with the correct file name
    assert len(list(demux_results.projects)) == 0
    # GIVEN the location of a demultiplexed flowcell that is not finished
    assert len(list(demux_results.raw_projects)) != 0

    # WHEN renaming the files
    post_demux_api.rename_files(demux_results=demux_results)

    # THEN assert that that the files have been renamed
    assert len(list(demux_results.projects)) != 0
    assert len(list(demux_results.raw_projects)) == 0

from pathlib import Path

from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingNovaseqAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


def test_rename_demux_result(
    demultiplexed_flow_cell_working_directory: Path,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
):
    # GIVEN that this is the location of the demultiplex api
    demultiplex_context.demultiplex_api_.out_dir = demultiplexed_flow_cell_working_directory
    post_demux_api: DemuxPostProcessingNovaseqAPI = DemuxPostProcessingNovaseqAPI(
        config=demultiplex_context
    )
    demux_dir: Path = demultiplexed_flow_cell_working_directory
    demux_results: DemuxResults = DemuxResults(
        demux_dir=demux_dir, flow_cell=bcl2fastq_flow_cell, bcl_converter="bcl2fastq"
    )
    # GIVEN that there are no projects with the correct file name
    assert not list(demux_results.projects)

    # GIVEN the location of a demultiplexed flowcell that is not finished
    assert list(demux_results.raw_projects)

    # WHEN renaming the files
    post_demux_api.rename_files(demux_results=demux_results)

    # THEN assert that the files have been renamed
    assert list(demux_results.projects)
    assert not list(demux_results.raw_projects)

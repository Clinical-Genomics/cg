from pathlib import Path
from typing import Dict, List
import pytest
from cg.store.models import Sample
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI
from cg.meta.demultiplex.housekeeper_storage_functions import add_sample_sheet_path_to_housekeeper
from cg.models.cg_config import CGConfig
from tests.meta.demultiplex.conftest import FlowCellInfo


def test_set_dry_run(
    demultiplex_context: CGConfig,
):
    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingAPI = DemuxPostProcessingAPI(config=demultiplex_context)

    # THEN dry run should be False
    assert post_demux_api.dry_run is False

    # WHEN dry run set to True
    post_demux_api.set_dry_run(dry_run=True)

    # THEN dry run should be True
    assert post_demux_api.dry_run is True


@pytest.mark.parametrize(
    "demux_type",
    ["BCL2FASTQ_TREE", "BCLCONVERT_TREE", "BCLCONVERT_FLAT", "BCLCONVERT_ON_SEQUENCER"],
)
def test_post_processing_of_flow_cell(
    demux_type: str,
    demultiplex_context: CGConfig,
    flow_cell_info_map: Dict[str, FlowCellInfo],
    tmp_demultiplexed_runs_directory: Path,
    novaseq6000_bcl_convert_sample_sheet_path,
):
    """Test adding a demultiplexed flow cell to the databases with. Runs on each type of
    demultiplexing software and setting used."""

    # GIVEN a demultiplexed flow cell
    flow_cell_demultiplexing_directory: str = flow_cell_info_map.get(demux_type).directory
    flow_cell_name: str = flow_cell_info_map.get(demux_type).name
    sample_internal_ids: List[str] = flow_cell_info_map.get(demux_type).sample_internal_ids

    # GIVEN the sample_internal_ids are present in statusdb
    for sample_internal_id in sample_internal_ids:
        assert demultiplex_context.status_db.get_sample_by_internal_id(sample_internal_id)

    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a directory with a flow cell demultiplexed with BCL Convert
    demux_post_processing_api.demultiplexed_runs_dir = tmp_demultiplexed_runs_directory

    # GIVEN that the sample sheet is in housekeeper
    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=Path(
            tmp_demultiplexed_runs_directory, flow_cell_demultiplexing_directory
        ),
        flow_cell_name=flow_cell_name,
        hk_api=demux_post_processing_api.hk_api,
    )

    # THEN the sample sheet is in housekeeper
    assert demux_post_processing_api.hk_api.get_files(
        bundle=flow_cell_name, tags=[SequencingFileTag.SAMPLE_SHEET]
    ).all()
    # WHEN post-processing the demultiplexed flow cell
    demux_post_processing_api.finish_flow_cell(flow_cell_demultiplexing_directory)

    # THEN a flow cell was created in statusdb
    assert demux_post_processing_api.status_db.get_flow_cell_by_name(flow_cell_name)

    # THEN sequencing metrics were created for the flow cell
    assert demux_post_processing_api.status_db.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell_name
    )
    # THEN the read count was calculated for all samples in the flow cell directory
    for sample_internal_id in sample_internal_ids:
        sample: Sample = demux_post_processing_api.status_db.get_sample_by_internal_id(
            sample_internal_id
        )
        assert isinstance(sample.reads, int)

    # THEN a bundle was added to Housekeeper for the flow cell
    assert demux_post_processing_api.hk_api.bundle(flow_cell_name)

    # THEN a bundle was added to Housekeeper for each sample
    for sample_internal_id in sample_internal_ids:
        assert demux_post_processing_api.hk_api.bundle(sample_internal_id)

    # THEN a sample sheet was added to Housekeeper
    assert demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.SAMPLE_SHEET],
        bundle=flow_cell_name,
    ).all()

    # THEN sample fastq files were added to Housekeeper tagged with FASTQ and the flow cell name
    for sample_internal_id in sample_internal_ids:
        assert demux_post_processing_api.hk_api.get_files(
            tags=[SequencingFileTag.FASTQ, flow_cell_name],
            bundle=sample_internal_id,
        ).all()

    # THEN a delivery file was created in the flow cell directory
    delivery_path = Path(
        demux_post_processing_api.demultiplexed_runs_dir,
        flow_cell_demultiplexing_directory,
        DemultiplexingDirsAndFiles.DELIVERY,
    )

    assert delivery_path.exists()


def test_get_all_demultiplexed_flow_cell_out_dirs(
    demultiplex_context: CGConfig,
    tmp_demultiplexed_runs_directory: Path,
    tmp_demultiplexed_runs_bcl2fastq_directory: Path,
):
    """Test returning all flow cell directories from the demultiplexing run directory."""
    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context
    demux_api: DemuxPostProcessingAPI = DemuxPostProcessingAPI(config=demultiplex_context)
    demux_api.demultiplexed_runs_dir = tmp_demultiplexed_runs_directory

    # WHEN calling get_all_demultiplexed_flow_cell_dirs
    demultiplexed_flow_cell_dirs: List[Path] = demux_api.get_all_demultiplexed_flow_cell_dirs()

    # THEN the demultiplexed flow cells run directories should be returned
    assert tmp_demultiplexed_runs_bcl2fastq_directory in demultiplexed_flow_cell_dirs

import logging
import os
from pathlib import Path
from typing import Dict, Generator, List

import pytest


from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI

from cg.models.cg_config import CGConfig

from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.store import Store

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
    ["BCL2FASTQ_TREE", "BCLCONVERT_TREE", "BCLCONVERT_FLAT"],
)
def test_post_processing_of_flow_cell(
    demux_type: str,
    demultiplex_context: CGConfig,
    flow_cell_info_map: Dict[str, FlowCellInfo],
    demultiplexed_flow_cells_tmp_directory: Path,
):
    """Test adding a demultiplexed flow cell to the databases with. Runs on each type of
    demultiplexing software and setting used."""

    # GIVEN a demultiplexed flow cell
    flow_cell_demultplexing_directory: str = flow_cell_info_map.get(demux_type).directory
    flow_cell_name: str = flow_cell_info_map.get(demux_type).name
    sample_internal_ids: List[str] = flow_cell_info_map.get(demux_type).sample_internal_ids

    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a directory with a flow cell demultiplexed with BCL Convert
    demux_post_processing_api.demux_api.out_dir = demultiplexed_flow_cells_tmp_directory

    # GIVEN that a sample sheet exists in the flow cell run directory
    path = Path(
        demux_post_processing_api.demux_api.run_dir,
        flow_cell_demultplexing_directory,
        DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME,
    )
    os.makedirs(path.parent, exist_ok=True)
    path.touch()

    # WHEN post processing the demultiplexed flow cell
    demux_post_processing_api.finish_flow_cell_temp(flow_cell_demultplexing_directory)

    # THEN a flow cell was created in statusdb
    assert demux_post_processing_api.status_db.get_flow_cell_by_name(flow_cell_name)

    # THEN sequencing metrics were created for the flow cell
    assert demux_post_processing_api.status_db.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell_name
    )
    # THEN the read count was calculated for all samples in the flow cell directory
    for sample_internal_id in sample_internal_ids:
        sample = demux_post_processing_api.status_db.get_sample_by_internal_id(sample_internal_id)
        assert sample is not None
        assert sample.calculated_read_count

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
        demux_post_processing_api.demux_api.out_dir,
        flow_cell_demultplexing_directory,
        DemultiplexingDirsAndFiles.DELIVERY,
    )

    assert delivery_path.exists()

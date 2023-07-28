from pathlib import Path
from typing import List


from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.demultiplex.demux_post_processing import (
    DemuxPostProcessingAPI,
)

from cg.models.cg_config import CGConfig


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


def test_post_processing_of_flow_cell_demultiplexed_with_bclconvert(
    demultiplex_context: CGConfig,
    flow_cell_directory_name_demultiplexed_with_bcl_convert: str,
    flow_cell_name_demultiplexed_with_bcl_convert: str,
    demultiplexed_flow_cells_tmp_directory: Path,
    bcl_convert_demultiplexed_flow_cell_sample_internal_ids: List[str],
    novaseq_6000_dir: Path,
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a directory with a flow cell demultiplexed with BCL Convert
    demux_post_processing_api.demux_api.out_dir = demultiplexed_flow_cells_tmp_directory
    demux_post_processing_api.demux_api.run_dir = novaseq_6000_dir

    # WHEN post processing the demultiplexed flow cell
    demux_post_processing_api.finish_flow_cell(
        flow_cell_directory_name_demultiplexed_with_bcl_convert
    )

    # THEN a flow cell was created in statusdb
    assert demux_post_processing_api.status_db.get_flow_cell_by_name(
        flow_cell_name_demultiplexed_with_bcl_convert
    )

    # THEN sequencing metrics were created for the flow cell
    assert demux_post_processing_api.status_db.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell_name_demultiplexed_with_bcl_convert
    )
    # THEN the read count was calculated for all samples in the flow cell directory
    for sample_id in bcl_convert_demultiplexed_flow_cell_sample_internal_ids:
        sample = demux_post_processing_api.status_db.get_sample_by_internal_id(sample_id)
        assert sample is not None
        assert sample.calculated_read_count

    # THEN a bundle was added to Housekeeper for the flow cell
    assert demux_post_processing_api.hk_api.bundle(flow_cell_name_demultiplexed_with_bcl_convert)

    # THEN a bundle was added to Housekeeper for each sample
    for sample_id in bcl_convert_demultiplexed_flow_cell_sample_internal_ids:
        assert demux_post_processing_api.hk_api.bundle(sample_id)

    # THEN a sample sheet was added to Housekeeper
    assert demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.SAMPLE_SHEET],
        bundle=flow_cell_name_demultiplexed_with_bcl_convert,
    ).all()

    # THEN sample fastq files were added to Housekeeper tagged with FASTQ and the flow cell name
    for sample_id in bcl_convert_demultiplexed_flow_cell_sample_internal_ids:
        assert demux_post_processing_api.hk_api.get_files(
            tags=[SequencingFileTag.FASTQ, flow_cell_name_demultiplexed_with_bcl_convert],
            bundle=sample_id,
        ).all()

    # THEN a delivery file was created in the flow cell directory
    delivery_path = Path(
        demux_post_processing_api.demux_api.out_dir,
        flow_cell_directory_name_demultiplexed_with_bcl_convert,
        DemultiplexingDirsAndFiles.DELIVERY,
    )

    assert delivery_path.exists()


def test_post_processing_of_flow_cell_demultiplexed_with_bcl2fastq(
    demultiplex_context: CGConfig,
    flow_cell_directory_name_demultiplexed_with_bcl2fastq: str,
    flow_cell_name_demultiplexed_with_bcl2fastq: str,
    demultiplexed_flow_cells_tmp_directory: Path,
    hiseq_dir: Path,
    bcl2fastq_demultiplexed_flow_cell_sample_internal_ids: List[str],
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a directory with a flow cell demultiplexed with bcl2fastq
    demux_post_processing_api.demux_api.out_dir = demultiplexed_flow_cells_tmp_directory
    demux_post_processing_api.demux_api.run_dir = hiseq_dir

    # WHEN post processing the demultiplexed flow cell
    demux_post_processing_api.finish_flow_cell(
        flow_cell_directory_name_demultiplexed_with_bcl2fastq
    )

    # THEN a flow cell was created in statusdb
    assert demux_post_processing_api.status_db.get_flow_cell_by_name(
        flow_cell_name_demultiplexed_with_bcl2fastq
    )

    # THEN sequencing metrics were created for the flow cell
    assert demux_post_processing_api.status_db.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell_name_demultiplexed_with_bcl2fastq
    )

    # THEN the read count was calculated for all samples in the flow cell directory
    for sample_internal_id in bcl2fastq_demultiplexed_flow_cell_sample_internal_ids:
        sample = demux_post_processing_api.status_db.get_sample_by_internal_id(sample_internal_id)
        assert sample is not None
        assert sample.calculated_read_count

    # THEN a bundle was added to Housekeeper for the flow cell
    assert demux_post_processing_api.hk_api.bundle(flow_cell_name_demultiplexed_with_bcl2fastq)

    # THEN a bundle was added to Housekeeper for each sample
    for sample_internal_id in bcl2fastq_demultiplexed_flow_cell_sample_internal_ids:
        assert demux_post_processing_api.hk_api.bundle(sample_internal_id)

    # THEN a sample sheet was added to Housekeeper
    assert demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.SAMPLE_SHEET],
        bundle=flow_cell_name_demultiplexed_with_bcl2fastq,
    ).all()

    # THEN sample fastq files were added to Housekeeper tagged with FASTQ and the flow cell name
    for sample_internal_id in bcl2fastq_demultiplexed_flow_cell_sample_internal_ids:
        assert demux_post_processing_api.hk_api.get_files(
            tags=[SequencingFileTag.FASTQ, flow_cell_name_demultiplexed_with_bcl2fastq],
            bundle=sample_internal_id,
        ).all()

    # THEN a delivery file was created in the flow cell directory
    delivery_path = Path(
        demux_post_processing_api.demux_api.out_dir,
        flow_cell_directory_name_demultiplexed_with_bcl2fastq,
        DemultiplexingDirsAndFiles.DELIVERY,
    )

    assert delivery_path.exists()

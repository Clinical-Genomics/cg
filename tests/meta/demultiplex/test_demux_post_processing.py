from pathlib import Path

import pytest
from housekeeper.store.models import File

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI
from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_and_include_sample_sheet_path_to_housekeeper,
)
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.store.models import Sample


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
    "flow_cell_fixture, sample_ids_fixture",
    [
        ("novaseq_x_flow_cell", "selected_novaseq_x_sample_ids"),
        (
            "novaseq_6000_post_1_5_kits_flow_cell",
            "selected_novaseq_6000_post_1_5_kits_sample_ids",
        ),
    ],
    ids=["BCLConvert on sequencer", "BCLConvert flat"],
)
def test_post_processing_of_flow_cell(
    flow_cell_fixture: str,
    sample_ids_fixture: str,
    updated_demultiplex_context: CGConfig,
    updated_demux_post_processing_api: DemuxPostProcessingAPI,
    tmp_illumina_demultiplexed_flow_cells_directory: Path,
    request: pytest.FixtureRequest,
):
    """Test adding a demultiplexed flow cell to the databases with. Runs on each type of
    demultiplexing software and setting used."""

    # GIVEN a demultiplexed flow cell
    flow_cell: IlluminaRunDirectoryData = request.getfixturevalue(flow_cell_fixture)
    flow_cell_demultiplexing_directory: str = flow_cell.full_name
    flow_cell_name: str = flow_cell.id
    sample_internal_ids: list[str] = request.getfixturevalue(sample_ids_fixture)

    # GIVEN the sample_internal_ids are present in statusdb
    for sample_internal_id in sample_internal_ids:
        assert updated_demultiplex_context.status_db.get_sample_by_internal_id(sample_internal_id)

    # GIVEN a DemuxPostProcessing API

    # GIVEN that the sample sheet is in housekeeper
    add_and_include_sample_sheet_path_to_housekeeper(
        flow_cell_directory=flow_cell.path,
        flow_cell_name=flow_cell_name,
        hk_api=updated_demux_post_processing_api.hk_api,
    )
    assert updated_demux_post_processing_api.hk_api.get_files(
        bundle=flow_cell_name, tags=[SequencingFileTag.SAMPLE_SHEET]
    ).all()

    # WHEN post-processing the demultiplexed flow cell
    updated_demux_post_processing_api.finish_flow_cell(flow_cell_demultiplexing_directory)

    # THEN a flow cell was created in statusdb
    assert updated_demux_post_processing_api.status_db.get_flow_cell_by_name(flow_cell_name)

    # THEN sequencing metrics were created for the flow cell
    assert updated_demux_post_processing_api.status_db.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell_name
    )
    # THEN the read count was calculated for all samples in the flow cell directory
    for sample_internal_id in sample_internal_ids:
        sample: Sample = updated_demux_post_processing_api.status_db.get_sample_by_internal_id(
            sample_internal_id
        )
        assert isinstance(sample.reads, int)

    # THEN a bundle was added to Housekeeper for the flow cell
    assert updated_demux_post_processing_api.hk_api.bundle(flow_cell_name)

    # THEN a bundle was added to Housekeeper for each sample
    for sample_internal_id in sample_internal_ids:
        assert updated_demux_post_processing_api.hk_api.bundle(sample_internal_id)

    # THEN a sample sheet was added to Housekeeper
    assert updated_demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.SAMPLE_SHEET],
        bundle=flow_cell_name,
    ).all()

    # THEN a run parameters file was added to Housekeeper
    assert updated_demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.RUN_PARAMETERS],
        bundle=flow_cell_name,
    ).all()

    # THEN sample fastq files were added to Housekeeper tagged with FASTQ and the flow cell name
    for sample_internal_id in sample_internal_ids:
        assert updated_demux_post_processing_api.hk_api.get_files(
            tags=[SequencingFileTag.FASTQ, flow_cell_name],
            bundle=sample_internal_id,
        ).all()

    # THEN a delivery file was created in the flow cell directory
    delivery_path = Path(
        updated_demux_post_processing_api.demultiplexed_runs_dir,
        flow_cell_demultiplexing_directory,
        DemultiplexingDirsAndFiles.DELIVERY,
    )

    assert delivery_path.exists()


def test_get_all_demultiplexed_flow_cell_out_dirs(
    demultiplex_context: CGConfig,
    tmp_illumina_demultiplexed_flow_cells_directory,
    hiseq_x_single_index_flow_cell_name: str,
):
    """Test returning all flow cell directories from the demultiplexing run directory."""
    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context
    demux_api: DemuxPostProcessingAPI = DemuxPostProcessingAPI(config=demultiplex_context)
    demux_api.demultiplexed_runs_dir = tmp_illumina_demultiplexed_flow_cells_directory

    # WHEN calling get_all_demultiplexed_flow_cell_dirs
    demultiplexed_flow_cell_dirs: list[Path] = demux_api.get_all_demultiplexed_flow_cell_dirs()

    # THEN the demultiplexed flow cells run directories should be returned
    demuxed_flow_cell_path = Path(
        tmp_illumina_demultiplexed_flow_cells_directory, hiseq_x_single_index_flow_cell_name
    )
    assert demuxed_flow_cell_path in demultiplexed_flow_cell_dirs


def test_post_processing_tracks_undetermined_fastq_files(
    updated_demux_post_processing_api: DemuxPostProcessingAPI,
    hiseq_x_single_index_flow_cell: IlluminaRunDirectoryData,
    selected_hiseq_x_single_index_sample_ids: list[str],
):
    # GIVEN a flow cell with undetermined fastqs in a non-pooled lane

    # GIVEN that the flow cell has the sample sheet in housekeeper
    add_and_include_sample_sheet_path_to_housekeeper(
        flow_cell_directory=hiseq_x_single_index_flow_cell.path,
        flow_cell_name=hiseq_x_single_index_flow_cell.id,
        hk_api=updated_demux_post_processing_api.hk_api,
    )

    # WHEN post processing the flow cell
    updated_demux_post_processing_api.finish_flow_cell(hiseq_x_single_index_flow_cell.full_name)

    # THEN the undetermined fastqs were stored in housekeeper
    sample_internal_id: str = selected_hiseq_x_single_index_sample_ids[0]
    fastq_files: list[File] = updated_demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.FASTQ],
        bundle=sample_internal_id,
    ).all()

    undetermined_fastq_files = [file for file in fastq_files if "Undetermined" in file.path]
    assert undetermined_fastq_files


def test_sample_read_count_update_is_idempotent(
    updated_demux_post_processing_api: DemuxPostProcessingAPI,
    hiseq_x_single_index_flow_cell: IlluminaRunDirectoryData,
    selected_hiseq_x_single_index_sample_ids: list[str],
):
    """Test that sample read counts are the same if the flow cell is processed twice."""

    # GIVEN a demultiplexed flow cell with the sample sheet in housekeeper
    add_and_include_sample_sheet_path_to_housekeeper(
        flow_cell_directory=hiseq_x_single_index_flow_cell.path,
        flow_cell_name=hiseq_x_single_index_flow_cell.id,
        hk_api=updated_demux_post_processing_api.hk_api,
    )

    # WHEN post processing the flow cell twice
    sample_internal_id: str = selected_hiseq_x_single_index_sample_ids[0]
    updated_demux_post_processing_api.finish_flow_cell(hiseq_x_single_index_flow_cell.full_name)
    first_sample_read_count: int = (
        updated_demux_post_processing_api.status_db.get_sample_by_internal_id(
            sample_internal_id
        ).reads
    )

    updated_demux_post_processing_api.finish_flow_cell(hiseq_x_single_index_flow_cell.full_name)
    second_sample_read_count: int = (
        updated_demux_post_processing_api.status_db.get_sample_by_internal_id(
            sample_internal_id
        ).reads
    )

    # THEN the sample read counts are not zero
    assert first_sample_read_count

    # THEN the sample read count is the same after the second post processing
    assert first_sample_read_count == second_sample_read_count

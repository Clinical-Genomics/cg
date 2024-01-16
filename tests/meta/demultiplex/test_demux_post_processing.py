from pathlib import Path

import pytest
from housekeeper.store.models import File
from pydantic import BaseModel

from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI
from cg.meta.demultiplex.housekeeper_storage_functions import add_sample_sheet_path_to_housekeeper
from cg.models.cg_config import CGConfig
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


class DemultiplexingScenario(BaseModel):
    flow_cell_directory: str
    flow_cell_name: str
    samples_ids: str
    bcl_converter: str = BclConverter.BCLCONVERT


@pytest.mark.parametrize(
    "scenario",
    [
        DemultiplexingScenario(
            flow_cell_directory="flow_cell_directory_name_demultiplexed_with_bcl_convert",
            flow_cell_name="flow_cell_name_demultiplexed_with_bcl_convert",
            samples_ids="bcl_convert_demultiplexed_flow_cell_sample_internal_ids",
        ),
        DemultiplexingScenario(
            flow_cell_directory="flow_cell_directory_name_demultiplexed_with_bcl2fastq",
            flow_cell_name="flow_cell_name_demultiplexed_with_bcl2fastq",
            samples_ids="bcl2fastq_demultiplexed_flow_cell_sample_internal_ids",
            bcl_converter=BclConverter.BCL2FASTQ,
        ),
        DemultiplexingScenario(
            flow_cell_directory="flow_cell_directory_name_demultiplexed_with_bcl_convert_on_sequencer",
            flow_cell_name="flow_cell_name_demultiplexed_with_bcl_convert_on_sequencer",
            samples_ids="bcl_convert_demultiplexed_flow_cell_sample_internal_ids",
        ),
        DemultiplexingScenario(
            flow_cell_directory="flow_cell_directory_name_demultiplexed_with_bcl_convert_flat",
            flow_cell_name="flow_cell_name_demultiplexed_with_bcl_convert",
            samples_ids="bcl_convert_demultiplexed_flow_cell_sample_internal_ids",
        ),
    ],
    ids=["BCLConvert tree", "BCL2FASTQ", "BCLConvert on sequencer", "BCLConvert flat"],
)
def test_post_processing_of_flow_cell(
    scenario: DemultiplexingScenario,
    demultiplex_context: CGConfig,
    request,
    tmp_demultiplexed_runs_directory: Path,
):
    """Test adding a demultiplexed flow cell to the databases with. Runs on each type of
    demultiplexing software and setting used."""

    # GIVEN a demultiplexed flow cell
    flow_cell_demultiplexing_directory: str = request.getfixturevalue(scenario.flow_cell_directory)
    flow_cell_name: str = request.getfixturevalue(scenario.flow_cell_name)
    sample_internal_ids: list[str] = request.getfixturevalue(scenario.samples_ids)

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
    demux_post_processing_api.finish_flow_cell(
        flow_cell_directory_name=flow_cell_demultiplexing_directory,
        bcl_converter=scenario.bcl_converter,
    )

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
    demultiplexed_flow_cell_dirs: list[Path] = demux_api.get_all_demultiplexed_flow_cell_dirs()

    # THEN the demultiplexed flow cells run directories should be returned
    assert tmp_demultiplexed_runs_bcl2fastq_directory in demultiplexed_flow_cell_dirs


def test_post_processing_tracks_undetermined_fastqs_for_bcl2fastq(
    demux_post_processing_api: DemuxPostProcessingAPI,
    bcl2fastq_flow_cell_dir_name: str,
    bcl2fastq_sample_id_with_non_pooled_undetermined_reads: str,
    bcl2fastq_non_pooled_sample_read_count: int,
):
    # GIVEN a flow cell with undetermined fastqs in a non-pooled lane

    # WHEN post processing the flow cell
    demux_post_processing_api.finish_flow_cell(
        flow_cell_directory_name=bcl2fastq_flow_cell_dir_name, bcl_converter=BclConverter.BCL2FASTQ
    )

    # THEN the undetermined fastqs were stored in housekeeper
    fastq_files: list[File] = demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.FASTQ],
        bundle=bcl2fastq_sample_id_with_non_pooled_undetermined_reads,
    ).all()

    undetermined_fastq_files = [file for file in fastq_files if "Undetermined" in file.path]
    assert undetermined_fastq_files

    # THEN the sample read count was updated with the undetermined reads
    sample: Sample = demux_post_processing_api.status_db.get_sample_by_internal_id(
        bcl2fastq_sample_id_with_non_pooled_undetermined_reads
    )
    assert sample.reads == bcl2fastq_non_pooled_sample_read_count


def test_post_processing_tracks_undetermined_fastqs_for_bclconvert(
    demux_post_processing_api: DemuxPostProcessingAPI,
    bclconvert_flow_cell_dir_name: str,
    bcl_convert_sample_id_with_non_pooled_undetermined_reads: str,
    bcl_convert_non_pooled_sample_read_count: int,
):
    # GIVEN a flow cell with undetermined fastqs in a non-pooled lane

    # WHEN post processing the flow cell
    demux_post_processing_api.finish_flow_cell(
        flow_cell_directory_name=bclconvert_flow_cell_dir_name,
        bcl_converter=BclConverter.BCLCONVERT,
    )

    # THEN the undetermined fastqs were stored in housekeeper
    fastq_files: list[File] = demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.FASTQ],
        bundle=bcl_convert_sample_id_with_non_pooled_undetermined_reads,
    ).all()

    undetermined_fastq_files = [file for file in fastq_files if "Undetermined" in file.path]
    assert undetermined_fastq_files

    # THEN the sample read count was updated with the undetermined reads
    sample: Sample = demux_post_processing_api.status_db.get_sample_by_internal_id(
        bcl_convert_sample_id_with_non_pooled_undetermined_reads
    )
    assert sample.reads == bcl_convert_non_pooled_sample_read_count


def test_sample_read_count_update_is_idempotent(
    demux_post_processing_api: DemuxPostProcessingAPI,
    bcl2fastq_flow_cell_dir_name: str,
    bcl2fastq_sample_id_with_non_pooled_undetermined_reads: str,
):
    """Test that sample read counts are the same if the flow cell is processed twice."""

    # GIVEN a demultiplexed flow cell

    # WHEN post processing the flow cell twice
    demux_post_processing_api.finish_flow_cell(
        flow_cell_directory_name=bcl2fastq_flow_cell_dir_name, bcl_converter=BclConverter.BCL2FASTQ
    )
    first_sample_read_count: int = demux_post_processing_api.status_db.get_sample_by_internal_id(
        bcl2fastq_sample_id_with_non_pooled_undetermined_reads
    ).reads

    demux_post_processing_api.finish_flow_cell(bcl2fastq_flow_cell_dir_name)
    second_sample_read_count: int = demux_post_processing_api.status_db.get_sample_by_internal_id(
        bcl2fastq_sample_id_with_non_pooled_undetermined_reads
    ).reads

    # THEN the sample read counts are not zero
    assert first_sample_read_count

    # THEN the sample read count is the same after the second post processing
    assert first_sample_read_count == second_sample_read_count

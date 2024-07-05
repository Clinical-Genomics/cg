"""Tests for the housekeeper storage functions of the demultiplexing post post-processing module."""

from pathlib import Path
from unittest.mock import PropertyMock, patch

from housekeeper.store.models import File

from cg.apps.demultiplex.sample_sheet.sample_sheet_models import SampleSheet
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina_services.illumina_post_processing_service.housekeeper_storage import (
    add_demux_logs_to_housekeeper,
    add_run_parameters_file_to_housekeeper,
    add_sample_fastq_files_to_housekeeper,
)
from cg.store.store import Store


def test_add_fastq_files_to_housekeeper(
    new_demultiplex_context: CGConfig,
    novaseq_6000_post_1_5_kits_flow_cell: IlluminaRunDirectoryData,
    novaseq_6000_post_1_5_kits_sample_sheet_with_selected_samples: SampleSheet,
    selected_novaseq_6000_post_1_5_kits_sample_ids: list[str],
    tmp_demultiplexed_novaseq_6000_post_1_5_kits_path: Path,
):
    """Test that the fastq files of a sequencing run are added to Housekeeper."""
    # GIVEN a Housekeeper API and a Store
    hk_api: HousekeeperAPI = new_demultiplex_context.housekeeper_api
    store: Store = new_demultiplex_context.status_db

    # GIVEN that there are no fastq files in housekeeper for the selected samples
    for sample_id in selected_novaseq_6000_post_1_5_kits_sample_ids:
        assert hk_api.get_files(tags=[SequencingFileTag.FASTQ], bundle=sample_id).count() == 0

    # GIVEN a demultiplexed run dir data with a sample sheet and samples
    with patch.object(
        target=IlluminaRunDirectoryData,
        attribute="sample_sheet",
        new_callable=PropertyMock(
            return_value=novaseq_6000_post_1_5_kits_sample_sheet_with_selected_samples
        ),
    ), patch.object(
        target=IlluminaRunDirectoryData,
        attribute="get_demultiplexed_runs_dir",
        return_value=tmp_demultiplexed_novaseq_6000_post_1_5_kits_path,
    ):

        # WHEN adding the sample fastq files to Housekeeper
        add_sample_fastq_files_to_housekeeper(
            run_directory_data=novaseq_6000_post_1_5_kits_flow_cell,
            hk_api=hk_api,
            store=store,
        )

    # THEN two fastq files per sample were added to Housekeeper
    for sample_id in selected_novaseq_6000_post_1_5_kits_sample_ids:
        fastq_files: list[File] = hk_api.get_files(
            tags=[SequencingFileTag.FASTQ],
            bundle=sample_id,
        ).all()
        assert fastq_files
        assert len(fastq_files) == 2
        assert isinstance(fastq_files[0], File)


def test_add_demux_logs_to_housekeeper(
    new_demultiplex_context: CGConfig,
    novaseq_6000_post_1_5_kits_flow_cell: IlluminaRunDirectoryData,
    demultiplex_log_file_names: list[str],
):
    """Test that the demultiplex log files of a sequencing run are added to Housekeeper."""
    # GIVEN a Housekeeper API
    hk_api: HousekeeperAPI = new_demultiplex_context.housekeeper_api

    # GIVEN a bundle and flow cell version exists in Housekeeper
    hk_api.add_bundle_and_version_if_non_existent(
        bundle_name=novaseq_6000_post_1_5_kits_flow_cell.id
    )

    # GIVEN that there are no log files in Housekeeper
    existing_logs: list[File] = hk_api.get_files(
        tags=[SequencingFileTag.DEMUX_LOG],
        bundle=novaseq_6000_post_1_5_kits_flow_cell.id,
    ).all()
    assert not existing_logs

    # WHEN adding the demux logs to Housekeeper
    add_demux_logs_to_housekeeper(
        run_directory_data=novaseq_6000_post_1_5_kits_flow_cell,
        hk_api=hk_api,
    )

    # THEN the demux log files were added to Housekeeper
    files: list[File] = hk_api.get_files(
        tags=[SequencingFileTag.DEMUX_LOG],
        bundle=novaseq_6000_post_1_5_kits_flow_cell.id,
    ).all()
    assert len(files) == 2
    for file in files:
        assert file.path.split("/")[-1] in demultiplex_log_file_names


def test_add_run_parameters_to_housekeeper(
    new_demultiplex_context: CGConfig, novaseq_x_flow_cell: IlluminaRunDirectoryData
):
    """Test that the run parameters file of a sequencing run is added to Housekeeper."""
    # GIVEN a flow cell with a run parameters file and a Housekeeper API
    hk_api = new_demultiplex_context.housekeeper_api

    # GIVEN that a run parameters file does not exist for the flow cell in Housekeeper
    assert not hk_api.files(tags=[SequencingFileTag.RUN_PARAMETERS, novaseq_x_flow_cell.id]).all()

    # GIVEN that a bundle and version exists in Housekeeper
    hk_api.add_bundle_and_version_if_non_existent(bundle_name=novaseq_x_flow_cell.id)

    # WHEN adding the run parameters file to Housekeeper
    add_run_parameters_file_to_housekeeper(
        run_directory_data=novaseq_x_flow_cell,
        hk_api=hk_api,
    )

    # THEN the run parameters file was added to Housekeeper
    run_parameters_file: File = hk_api.files(
        tags=[SequencingFileTag.RUN_PARAMETERS, novaseq_x_flow_cell.id]
    ).first()
    assert run_parameters_file.path.endswith(DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE)

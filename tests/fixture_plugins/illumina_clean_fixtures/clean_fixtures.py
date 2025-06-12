from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.models.cg_config import CGConfig
from cg.services.illumina.cleaning.clean_runs_service import (
    IlluminaCleanRunsService,
)
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.store.models import IlluminaSequencingRun
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture(scope="function")
def illumina_clean_service_can_be_removed(
    tmp_sequencing_run_to_clean_path: Path,
    store_with_illumina_sequencing_data: Store,
    selected_novaseq_6000_pre_1_5_kits_sample_ids: str,
    housekeeper_api_with_illumina_seq_run_to_clean: HousekeeperAPI,
    tmp_sample_sheet_clean_illumina_sequencing_run_path: Path,
    tmp_sequencing_run_to_clean: IlluminaRunDirectoryData,
) -> IlluminaCleanRunsService:
    """Return a IlluminaCleanRunsService with a sequencing run that can be removed."""
    sequencing_run_to_clean: IlluminaSequencingRun = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_run_by_device_internal_id(
            tmp_sequencing_run_to_clean.id
        )
    )
    sequencing_run_to_clean.has_backup = True

    # Remove a sample metric to fulfill the cleaning criteria
    sample_metric_to_delete = [
        metric
        for metric in sequencing_run_to_clean.sample_metrics
        if metric.sample.internal_id == selected_novaseq_6000_pre_1_5_kits_sample_ids[1]
    ]
    store_with_illumina_sequencing_data.session.delete(sample_metric_to_delete[0])
    clean_flow_cell_api = IlluminaCleanRunsService(
        sequencing_run_path=tmp_sequencing_run_to_clean_path,
        status_db=store_with_illumina_sequencing_data,
        housekeeper_api=housekeeper_api_with_illumina_seq_run_to_clean,
        dry_run=False,
    )
    clean_flow_cell_api.sequencing_run_dir_data._sample_sheet_path_hk = (
        tmp_sample_sheet_clean_illumina_sequencing_run_path
    )
    return clean_flow_cell_api


@pytest.fixture(scope="function")
def illumina_clean_service_can_not_be_removed(
    tmp_sequencing_run_not_to_clean_path: Path,
    store_with_illumina_sequencing_data: Store,
    housekeeper_api_with_sequencing_run_not_to_clean: HousekeeperAPI,
) -> IlluminaCleanRunsService:
    """Return a IlluminaCleanRunsService with a sequencing run that can not be removed."""
    return IlluminaCleanRunsService(
        sequencing_run_path=tmp_sequencing_run_not_to_clean_path,
        status_db=store_with_illumina_sequencing_data,
        housekeeper_api=housekeeper_api_with_sequencing_run_not_to_clean,
        dry_run=False,
    )


@pytest.fixture(scope="function")
def tmp_clean_dir(tmp_path: Path) -> Path:
    """Return a temporary directory for cleaning."""
    clean_path = Path(tmp_path, "clean")
    clean_path.mkdir()
    return clean_path


@pytest.fixture(scope="function")
def tmp_sequencing_run_to_clean_path(
    tmp_novaseq_6000_pre_1_5_kits_flow_cell_path: Path, tmp_clean_dir: Path
) -> Path:
    """Returns the path to a sequencing run fulfilling all cleaning criteria."""
    clean_seq_run_path = Path(tmp_clean_dir, tmp_novaseq_6000_pre_1_5_kits_flow_cell_path.name)
    clean_seq_run_path.mkdir()
    return clean_seq_run_path


@pytest.fixture(scope="function")
def tmp_sequencing_run_to_clean(
    tmp_sequencing_run_to_clean_path: Path,
) -> IlluminaRunDirectoryData:
    """Returns a IlluminaRunDirectoryData object for a sequencing run that fulfills all cleaning criteria."""
    return IlluminaRunDirectoryData(tmp_sequencing_run_to_clean_path)


@pytest.fixture(scope="function")
def tmp_sequencing_run_not_to_clean_path(tmp_novaseq_6000_pre_1_5_kits_flow_cell_path: Path):
    """Return the path to a sequencing run not fulfilling all cleaning criteria."""
    return tmp_novaseq_6000_pre_1_5_kits_flow_cell_path


@pytest.fixture(scope="function")
def tmp_sequencing_run_not_to_clean(
    tmp_sequencing_run_not_to_clean_path: Path,
) -> IlluminaRunDirectoryData:
    """Returns a IlluminaRunDirectoryData object for a sequencing run that does not fulfill all cleaning criteria."""
    return IlluminaRunDirectoryData(tmp_sequencing_run_not_to_clean_path)


@pytest.fixture(scope="session")
def tmp_sample_sheet_clean_illumina_sequencing_run_path(tmp_path_factory) -> Path:
    sample_sheet_path: Path = tmp_path_factory.mktemp("SampleSheet.csv")
    return sample_sheet_path


@pytest.fixture(scope="function")
def housekeeper_api_with_illumina_seq_run_to_clean(
    real_housekeeper_api: HousekeeperAPI,
    helpers: StoreHelpers,
    hk_illumina_sequencing_run_bundle_to_clean: dict,
    hk_sample_bundle_for_illumina_sequencing_run_to_clean: dict,
) -> HousekeeperAPI:
    """
    Return a housekeeper api that contains a flow cell bundle with sample sheet,
    a sample bundle with a fastq and a SPRING file that are tagged with the flow cell.
    """
    helpers.ensure_hk_bundle(
        store=real_housekeeper_api, bundle_data=hk_illumina_sequencing_run_bundle_to_clean
    )
    helpers.ensure_hk_bundle(
        store=real_housekeeper_api,
        bundle_data=hk_sample_bundle_for_illumina_sequencing_run_to_clean,
    )
    return real_housekeeper_api


@pytest.fixture(scope="function")
def housekeeper_api_with_sequencing_run_not_to_clean(
    real_housekeeper_api: HousekeeperAPI,
    helpers: StoreHelpers,
    hk_sample_bundle_for_sequencing_run_not_to_clean: dict,
) -> HousekeeperAPI:
    """
    Return a housekeeper api that contains a flow cell bundle with sample sheet,
    a sample bundle with a fastq and a SPRING file that are tagged with the flow cell name.
    """
    helpers.ensure_hk_bundle(
        store=real_housekeeper_api, bundle_data=hk_sample_bundle_for_sequencing_run_not_to_clean
    )
    return real_housekeeper_api


@pytest.fixture(scope="function")
def hk_illumina_sequencing_run_bundle_to_clean(
    tmp_sequencing_run_to_clean: IlluminaRunDirectoryData,
    timestamp_yesterday: datetime,
    tmp_sample_sheet_clean_illumina_sequencing_run_path: Path,
) -> dict:
    """Housekeeper bundle information for a flow cell that can be cleaned."""
    return {
        "name": tmp_sequencing_run_to_clean.id,
        "created": timestamp_yesterday,
        "expires": timestamp_yesterday,
        "files": [
            {
                "path": str(tmp_sample_sheet_clean_illumina_sequencing_run_path),
                "archive": False,
                "tags": ["samplesheet", tmp_sequencing_run_to_clean.id],
            }
        ],
    }


@pytest.fixture(scope="function")
def hk_sample_bundle_for_illumina_sequencing_run_to_clean(
    selected_novaseq_6000_pre_1_5_kits_sample_ids: str,
    timestamp_yesterday: datetime,
    spring_file: Path,
    fastq_file: Path,
    spring_meta_data_file: Path,
    tmp_sequencing_run_to_clean: IlluminaRunDirectoryData,
) -> dict:
    return {
        "name": selected_novaseq_6000_pre_1_5_kits_sample_ids[0],
        "created": timestamp_yesterday,
        "expires": timestamp_yesterday,
        "files": [
            {
                "path": spring_file.as_posix(),
                "archive": False,
                "tags": [
                    SequencingFileTag.SPRING,
                    selected_novaseq_6000_pre_1_5_kits_sample_ids[0],
                    tmp_sequencing_run_to_clean.id,
                ],
            },
            {
                "path": fastq_file.as_posix(),
                "archive": False,
                "tags": [
                    SequencingFileTag.FASTQ,
                    selected_novaseq_6000_pre_1_5_kits_sample_ids[0],
                    tmp_sequencing_run_to_clean.id,
                ],
            },
            {
                "path": spring_meta_data_file.as_posix(),
                "archive": False,
                "tags": [
                    SequencingFileTag.SPRING_METADATA,
                    selected_novaseq_6000_pre_1_5_kits_sample_ids[0],
                    tmp_sequencing_run_to_clean.id,
                ],
            },
        ],
    }


@pytest.fixture(scope="function")
def hk_sample_bundle_for_sequencing_run_not_to_clean(
    sample_id: str,
    timestamp_yesterday: datetime,
) -> dict:
    return {
        "name": sample_id,
        "created": timestamp_yesterday,
        "expires": timestamp_yesterday,
        "files": [],
    }


@pytest.fixture(scope="function")
def clean_illumina_sequencing_runs_context(
    cg_context: CGConfig,
    tmp_clean_dir: Path,
    tmp_sequencing_run_to_clean: IlluminaRunDirectoryData,
    store_with_illumina_sequencing_data: Store,
    housekeeper_api_with_illumina_seq_run_to_clean: HousekeeperAPI,
    selected_novaseq_6000_pre_1_5_kits_sample_ids: list[str],
) -> CGConfig:
    cg_context.run_instruments.illumina.sequencing_runs_dir = tmp_clean_dir
    cg_context.run_instruments.illumina.demultiplexed_runs_dir = tmp_clean_dir
    cg_context.housekeeper_api_ = housekeeper_api_with_illumina_seq_run_to_clean

    sequencing_run: IlluminaSequencingRun = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_run_by_device_internal_id(
            tmp_sequencing_run_to_clean.id
        )
    )
    sequencing_run.has_backup = True
    sample_metric_to_delete = [
        metric
        for metric in sequencing_run.sample_metrics
        if metric.sample.internal_id == selected_novaseq_6000_pre_1_5_kits_sample_ids[1]
    ]
    store_with_illumina_sequencing_data.session.delete(sample_metric_to_delete[0])
    cg_context.status_db_ = store_with_illumina_sequencing_data

    return cg_context

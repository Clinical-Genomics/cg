"""Tests for the CleanFlowCellsAPI."""
from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.clean.clean_flow_cells import CleanFlowCellAPI
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData
from cg.store import Store
from cg.store.models import Flowcell, Sample
from tests.store_helpers import StoreHelpers


@pytest.fixture(scope="function")
def flow_cell_clean_api_can_be_removed(
    tmp_flow_cell_to_clean_path: Path,
    store_with_flow_cell_to_clean: Store,
    housekeeper_api_with_flow_cell_to_clean: HousekeeperAPI,
    tmp_sample_sheet_clean_flow_cell_path: Path,
) -> CleanFlowCellAPI:
    """Return a CleanFlowCellAPI with a flow cell that can be removed."""
    clean_flow_cell_api = CleanFlowCellAPI(
        flow_cell_path=tmp_flow_cell_to_clean_path,
        status_db=store_with_flow_cell_to_clean,
        housekeeper_api=housekeeper_api_with_flow_cell_to_clean,
        dry_run=False,
    )
    clean_flow_cell_api.flow_cell._sample_sheet_path_hk = tmp_sample_sheet_clean_flow_cell_path
    return clean_flow_cell_api


@pytest.fixture(scope="function")
def flow_cell_clean_api_can_not_be_removed(
    tmp_flow_cell_not_to_clean_path: Path,
    store_with_flow_cell_not_to_clean: Store,
    real_housekeeper_api: HousekeeperAPI,
) -> CleanFlowCellAPI:
    """Return a CleanFlowCellAPI with a flow cell that can not be removed."""
    return CleanFlowCellAPI(
        flow_cell_path=tmp_flow_cell_not_to_clean_path,
        status_db=store_with_flow_cell_not_to_clean,
        housekeeper_api=real_housekeeper_api,
        dry_run=False,
    )


@pytest.fixture(scope="function")
def tmp_flow_cell_to_clean_path(tmp_flow_cell_directory_bclconvert: Path):
    """Returns the path to a flow cell fulfilling all cleaning criteria."""
    return tmp_flow_cell_directory_bclconvert


@pytest.fixture(scope="function")
def tmp_flow_cell_to_clean(tmp_flow_cell_to_clean_path: Path) -> FlowCellDirectoryData:
    """Returns a flow cell directory object for a flow cell that fulfills all cleaning criteria."""
    return FlowCellDirectoryData(tmp_flow_cell_to_clean_path)


@pytest.fixture(scope="function")
def tmp_flow_cell_not_to_clean_path(tmp_flow_cell_directory_bcl2fastq: Path):
    """Return the path to a flow cell not fulfilling all cleaning criteria."""
    return tmp_flow_cell_directory_bcl2fastq


@pytest.fixture(scope="function")
def tmp_flow_cell_not_to_clean(tmp_flow_cell_not_to_clean_path: Path) -> FlowCellDirectoryData:
    """Returns a flow cell directory object for a flow cell that does not fulfill all cleaning criteria."""
    return FlowCellDirectoryData(tmp_flow_cell_not_to_clean_path)


@pytest.fixture(scope="session")
def tmp_sample_sheet_clean_flow_cell_path(tmp_path_factory) -> Path:
    sample_sheet_path = tmp_path_factory.mktemp("SampleSheet.csv")
    return sample_sheet_path


@pytest.fixture
def store_with_flow_cell_to_clean(
    store: Store,
    sample_id: str,
    tmp_flow_cell_to_clean: FlowCellDirectoryData,
    helpers: StoreHelpers,
) -> Store:
    """Return a store with multiple samples with sample lane sequencing metrics."""
    sample_sequencing_metrics_details: list[str | int | float] = [
        (sample_id, tmp_flow_cell_to_clean.id, 1, 50_000_0000, 90.5, 32),
        (sample_id, tmp_flow_cell_to_clean.id, 2, 50_000_0000, 90.4, 31),
    ]
    flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=tmp_flow_cell_to_clean.id,
        store=store,
        has_backup=True,
    )
    sample: Sample = helpers.add_sample(
        name=sample_id, internal_id=sample_id, sex="male", store=store, customer_id="cust500"
    )
    helpers.add_multiple_sample_lane_sequencing_metrics_entries(
        metrics_data=sample_sequencing_metrics_details, store=store
    )
    flow_cell.samples = [sample]
    store.session.add(flow_cell)
    store.session.commit()
    return store


@pytest.fixture
def store_with_flow_cell_not_to_clean(
    store: Store,
    sample_id: str,
    tmp_flow_cell_not_to_clean: FlowCellDirectoryData,
    helpers: StoreHelpers,
) -> Store:
    """Return a store with multiple samples with sample lane sequencing metrics."""
    sample_sequencing_metrics_details: list[str | int | float] = [
        (sample_id, tmp_flow_cell_not_to_clean.id, 1, 50_000_0000, 90.5, 32),
        (sample_id, tmp_flow_cell_not_to_clean.id, 2, 50_000_0000, 90.4, 31),
    ]
    flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=tmp_flow_cell_not_to_clean.id,
        store=store,
        has_backup=True,
    )
    sample: Sample = helpers.add_sample(
        name=sample_id, internal_id=sample_id, sex="male", store=store, customer_id="cust500"
    )
    helpers.add_multiple_sample_lane_sequencing_metrics_entries(
        metrics_data=sample_sequencing_metrics_details, store=store
    )
    flow_cell.samples = [sample]
    store.session.add(flow_cell)
    store.session.commit()
    return store


@pytest.fixture(scope="function")
def housekeeper_api_with_flow_cell_to_clean(
    real_housekeeper_api: HousekeeperAPI,
    helpers: StoreHelpers,
    hk_flow_cell_to_clean_bundle: dict,
    hk_sample_bundle_for_flow_cell_to_clean: dict,
) -> HousekeeperAPI:
    """
    Return a housekeeper api that contains a flow cell bundle with sample sheet,
    a sample bundle with a fastq and a SPRING file that are tagged with the flow cell.
    """
    helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=hk_flow_cell_to_clean_bundle)
    helpers.ensure_hk_bundle(
        store=real_housekeeper_api, bundle_data=hk_sample_bundle_for_flow_cell_to_clean
    )
    return real_housekeeper_api


@pytest.fixture(scope="function")
def housekeeper_api_with_flow_cell_not_to_clean(
    real_housekeeper_api: HousekeeperAPI,
    helpers: StoreHelpers,
    hk_sample_bundle_for_flow_cell_not_to_clean: dict,
) -> HousekeeperAPI:
    """
    Return a housekeeper api that contains a flow cell bundle with sample sheet,
    a sample bundle with a fastq and a SPRING file that are tagged with the flow cell.
    """
    helpers.ensure_hk_bundle(
        store=real_housekeeper_api, bundle_data=hk_sample_bundle_for_flow_cell_not_to_clean
    )
    return real_housekeeper_api


@pytest.fixture(scope="function")
def hk_flow_cell_to_clean_bundle(
    tmp_flow_cell_to_clean: FlowCellDirectoryData,
    timestamp_yesterday: datetime,
    tmp_sample_sheet_clean_flow_cell_path: Path,
) -> dict:
    """Housekeeper bundle information for a flow cell that can be cleaned."""
    return {
        "name": tmp_flow_cell_to_clean.id,
        "created": timestamp_yesterday,
        "expires": timestamp_yesterday,
        "files": [
            {
                "path": str(tmp_sample_sheet_clean_flow_cell_path),
                "archive": False,
                "tags": ["samplesheet", tmp_flow_cell_to_clean.id],
            }
        ],
    }


@pytest.fixture(scope="function")
def hk_sample_bundle_for_flow_cell_to_clean(
    sample_id: str,
    timestamp_yesterday: datetime,
    spring_file: Path,
    fastq_file: Path,
    spring_meta_data_file: Path,
    tmp_flow_cell_to_clean: FlowCellDirectoryData,
) -> dict:
    return {
        "name": sample_id,
        "created": timestamp_yesterday,
        "expires": timestamp_yesterday,
        "files": [
            {
                "path": spring_file.as_posix(),
                "archive": False,
                "tags": [SequencingFileTag.SPRING, sample_id, tmp_flow_cell_to_clean.id],
            },
            {
                "path": fastq_file.as_posix(),
                "archive": False,
                "tags": [SequencingFileTag.FASTQ, sample_id, tmp_flow_cell_to_clean.id],
            },
            {
                "path": spring_meta_data_file.as_posix(),
                "archive": False,
                "tags": [SequencingFileTag.SPRING_METADATA, sample_id, tmp_flow_cell_to_clean.id],
            },
        ],
    }


@pytest.fixture(scope="function")
def hk_sample_bundle_for_flow_cell_not_to_clean(
    sample_id: str,
    timestamp_yesterday: datetime,
) -> dict:
    return {
        "name": sample_id,
        "created": timestamp_yesterday,
        "expires": timestamp_yesterday,
        "files": [],
    }

"""Tests for transfer flow cell data."""
from datetime import datetime
import warnings
from pathlib import Path
from typing import Generator

from sqlalchemy import exc as sa_exc

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FlowCellStatus, SequencingFileTag
from cg.meta.transfer import TransferFlowCell
from cg.models.cgstats.flowcell import StatsFlowcell
from cg.store import Store
from cg.store.models import Flowcell
from tests.store_helpers import StoreHelpers


def test_add_tag_to_housekeeper(
    flow_cell_id: str, transfer_flow_cell_api: Generator[TransferFlowCell, None, None]
):
    """Test adding tag to Housekeeper."""
    # GIVEN transfer flow cell API

    # GIVEN no flow cell id tag in Housekeeper
    assert transfer_flow_cell_api.hk.tag(name=flow_cell_id) is None

    # WHEN adding tags to Housekeeper
    transfer_flow_cell_api._add_tag_to_housekeeper(
        store=True, tags=[SequencingFileTag.FASTQ, SequencingFileTag.SAMPLESHEET, flow_cell_id]
    )

    # THEN tha tags should be added
    assert transfer_flow_cell_api.hk.tag(name=flow_cell_id) is not None


def test_add_flow_cell_to_status_db(
    yet_another_flow_cell_id: str, transfer_flow_cell_api: Generator[TransferFlowCell, None, None]
):
    """Test adding flow cell to Status db."""
    # GIVEN transfer flow cell API

    # GIVEN a flow cell that does not exist in status db
    flow_cell: Flowcell = transfer_flow_cell_api.db.get_flow_cell(
        flow_cell_id=yet_another_flow_cell_id
    )

    assert flow_cell is None

    # GIVEN a cgstats flow cell
    cgstats_flow_cell: StatsFlowcell = transfer_flow_cell_api.stats.flowcell(
        yet_another_flow_cell_id
    )

    # WHEN adding flow cell to status db
    added_flow_cell: Flowcell = transfer_flow_cell_api._add_flow_cell_to_status_db(
        cgstats_flow_cell=cgstats_flow_cell,
        flow_cell=flow_cell,
        flow_cell_id=yet_another_flow_cell_id,
    )

    # THEN the tags should be added
    assert added_flow_cell.name == yet_another_flow_cell_id


def test_add_flow_cell_to_status_db_existing_flow_cell(
    flowcell_store: Store,
    flow_cell_id: str,
    helpers: StoreHelpers,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
):
    """Test adding flow cell to Status db, when already present."""
    # GIVEN transfer flow cell API

    # GIVEN a flow cell that exist in status db
    helpers.add_flowcell(store=flowcell_store, flow_cell_id=flow_cell_id)
    flow_cell: Flowcell = transfer_flow_cell_api.db.get_flow_cell(flow_cell_id=flow_cell_id)

    assert flow_cell is not None

    # GIVEN a cgstats flow cell
    cgstats_flow_cell: StatsFlowcell = transfer_flow_cell_api.stats.flowcell(flow_cell_id)

    # WHEN adding flow cell to status db
    added_flow_cell: Flowcell = transfer_flow_cell_api._add_flow_cell_to_status_db(
        cgstats_flow_cell=cgstats_flow_cell, flow_cell=flow_cell, flow_cell_id=flow_cell_id
    )

    # THEN flow cell should be returned should be identical to the one supplied
    assert added_flow_cell is flow_cell


def test_transfer(
    create_sample_sheet_file: Generator[Path, None, None],
    flowcell_store: Store,
    mocker,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
    yet_another_flow_cell_id: str,
):
    """Test transfer of sequencing files."""

    # GIVEN a store with a received but not sequenced sample
    housekeeper_api: HousekeeperAPI = transfer_flow_cell_api.hk
    assert flowcell_store.samples().count() == 2
    assert flowcell_store.flowcells().count() == 0
    assert housekeeper_api.bundles().count() == 0

    # GIVEN a sample sheet
    mocker.patch.object(TransferFlowCell, "_sample_sheet_path")
    TransferFlowCell._sample_sheet_path.return_value = create_sample_sheet_file

    # WHEN transferring the flowcell containing the sample
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        flow_cell = transfer_flow_cell_api.transfer(flow_cell_id=yet_another_flow_cell_id)

    # THEN it should create a new flowcell record
    assert flowcell_store.flowcells().count() == 1
    assert flow_cell.status == FlowCellStatus.ONDISK
    assert isinstance(flow_cell.id, int)
    assert flow_cell.name == yet_another_flow_cell_id
    status_sample = flowcell_store.samples().first()
    assert isinstance(status_sample.sequenced_at, datetime)

    # ... and it should store the fastq files and samplesheet for the sample in housekeeper
    hk_bundle = housekeeper_api.bundle(name=status_sample.internal_id)

    assert len(hk_bundle.versions[0].files) > 0
    assert (
        len([hk_file for hk_file in hk_bundle.versions[0].files if hk_file.path.endswith("csv")])
        == 1
    )

    for hk_file in hk_bundle.versions[0].files:
        assert hk_file.path.endswith("fastq.gz") or hk_file.path.endswith("csv")

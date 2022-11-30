"""Tests for transfer flow cell data."""
from datetime import datetime
import warnings
from pathlib import Path
from typing import Generator

from sqlalchemy import exc as sa_exc

from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FlowCellStatus, SequencingFileTag
from cg.meta.transfer import TransferFlowCell
from cg.meta.transfer.flowcell import _set_status_db_sample_sequenced_at
from cg.models.cgstats.flowcell import StatsFlowcell
from cg.store import Store
from cg.store.models import Flowcell, Sample
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


def test_add_sample_sheet_to_housekeeper_when_not_existing(
    caplog,
    create_sample_sheet_file: Generator[Path, None, None],
    flow_cell_id: str,
    mocker,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
):
    """Test adding sample sheet to Housekeeper when none can be found."""
    # GIVEN transfer flow cell API

    # GIVEN a sample sheet tag in Housekeeper
    transfer_flow_cell_api._add_tag_to_housekeeper(store=True, tags=[SequencingFileTag.SAMPLESHEET])

    mocker.patch.object(StatsAPI, "run_name")
    StatsAPI.run_name.return_value = flow_cell_id

    # WHEN adding sample sheet to Housekeeper
    transfer_flow_cell_api._add_sample_sheet_to_housekeeper(flow_cell_id=flow_cell_id, store=True)

    # THEN tha sample sheet should not be found
    assert "Unable to find sample sheet:" in caplog.text


def test_add_sample_sheet_to_housekeeper(
    caplog,
    create_sample_sheet_file: Generator[Path, None, None],
    flow_cell_id: str,
    mocker,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
):
    """Test adding sample sheet to Housekeeper."""
    # GIVEN transfer flow cell API

    # GIVEN a sample sheet tag in Housekeeper
    transfer_flow_cell_api._add_tag_to_housekeeper(store=True, tags=[SequencingFileTag.SAMPLESHEET])

    # GIVEN no flow cell id bundle in housekeeper
    hk_bundle = transfer_flow_cell_api.hk.bundle(name=SequencingFileTag.SAMPLESHEET)
    assert hk_bundle is None

    mocker.patch.object(StatsAPI, "run_name")
    StatsAPI.run_name.return_value = flow_cell_id

    # GIVEN a sample sheet that exists
    sample_sheet_path_dir: Path = Path("tests", "fixtures", "DEMUX", "HVKJCDRXX", "NAADM1")

    sample_sheet_path_dir.mkdir(parents=True, exist_ok=True)

    sample_sheet_file: Path = Path(sample_sheet_path_dir, "SampleSheet.csv")

    sample_sheet_file.touch()

    # WHEN adding sample sheet to Housekeeper
    transfer_flow_cell_api._add_sample_sheet_to_housekeeper(flow_cell_id=flow_cell_id, store=True)

    # Clean-up
    sample_sheet_file.unlink()

    # THEN tha sample sheet should be added to Housekeeper
    hk_bundle = transfer_flow_cell_api.hk.bundle(name=SequencingFileTag.SAMPLESHEET)
    for hk_file in hk_bundle.versions[0].files:
        assert hk_file.path.endswith("csv")


def test_set_status_db_sample_sequenced_at_when_first_sequenced(
    base_store: Store, flow_cell_id: str, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test setting sample sequenced at with no previous sequencing."""
    # GIVEN a status db sample
    sample: Sample = helpers.add_sample(base_store, sequenced_at=None)

    # Given no previous sequencing
    assert sample.sequenced_at is None

    # WHEN setting sequenced at for the sample
    _set_status_db_sample_sequenced_at(
        status_db_sample=sample, flow_cell_sequenced_at=timestamp_now
    )

    # THEN the sample sequenced at should be set
    assert sample.sequenced_at == timestamp_now


def test_set_status_db_sample_sequenced_at_when_sequenced_again(
    base_store: Store,
    flow_cell_id: str,
    helpers: StoreHelpers,
    timestamp_now: datetime,
    timestamp_yesterday: datetime,
):
    """Test setting sample sequenced at when sequenced again."""
    # GIVEN a status db sample sequenced yesterday
    sample: Sample = helpers.add_sample(base_store, sequenced_at=timestamp_yesterday)

    # WHEN setting sequenced at for the sample
    _set_status_db_sample_sequenced_at(
        status_db_sample=sample, flow_cell_sequenced_at=timestamp_now
    )

    # THEN the sample sequenced at should be set to today
    assert sample.sequenced_at == timestamp_now


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

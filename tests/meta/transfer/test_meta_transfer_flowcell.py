"""Tests for transfer flow cell data."""
from datetime import datetime
import logging
import warnings
from pathlib import Path
from typing import Generator

from sqlalchemy import exc as sa_exc

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FlowCellStatus, SequencingFileTag
from cg.meta.transfer import TransferFlowCell
from cg.meta.transfer.flowcell import _set_status_db_sample_sequenced_at, log_enough_reads
from cg.models.cgstats.flowcell import StatsFlowcell
from cg.models.demultiplex.demux_results import DemuxResults
from cg.store import Store
from cg.store.models import Flowcell, Sample
from tests.store_helpers import StoreHelpers


def test_add_tags_to_housekeeper(
    flow_cell_id: str, transfer_flow_cell_api: Generator[TransferFlowCell, None, None]
):
    """Test adding tag to Housekeeper."""
    # GIVEN transfer flow cell API

    # GIVEN no flow cell id tag in Housekeeper
    assert transfer_flow_cell_api.hk.tag(name=flow_cell_id) is None

    # WHEN adding tags to Housekeeper
    transfer_flow_cell_api._add_tags_to_housekeeper(
        store=True, tags=[SequencingFileTag.FASTQ, SequencingFileTag.SAMPLE_SHEET, flow_cell_id]
    )

    # THEN tha tags should be added
    assert transfer_flow_cell_api.hk.tag(name=flow_cell_id) is not None


def test_add_flow_cell_to_status_db(
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None], yet_another_flow_cell_id: str
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

    # THEN the flow cell added/returned should have the same id
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


def test_include_sample_sheet_to_housekeeper_when_not_existing(
    caplog,
    flow_cell_id: str,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
):
    """Test including sample sheet to Housekeeper when none can be found."""
    # GIVEN transfer flow cell API

    # GIVEN a sample sheet tag in Housekeeper
    transfer_flow_cell_api._add_tags_to_housekeeper(
        store=True, tags=[SequencingFileTag.SAMPLE_SHEET]
    )

    # WHEN including sample sheet to Housekeeper
    transfer_flow_cell_api._include_sample_sheet_to_housekeeper(
        flow_cell_dir=Path("does_not_exist"), flow_cell_id=flow_cell_id, store=True
    )

    # THEN tha sample sheet should not be found
    assert "Unable to find file:" in caplog.text


def test_include_sample_sheet_to_housekeeper(
    flow_cell_id: str,
    sample_sheet_path: Generator[Path, None, None],
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
):
    """Test including sample sheet to Housekeeper."""
    # GIVEN transfer flow cell API

    # GIVEN a sample sheet tag in Housekeeper
    transfer_flow_cell_api._add_tags_to_housekeeper(
        store=True, tags=[SequencingFileTag.SAMPLE_SHEET]
    )

    # GIVEN no flow cell id bundle in housekeeper
    hk_bundle = transfer_flow_cell_api.hk.bundle(name=SequencingFileTag.SAMPLE_SHEET)
    assert hk_bundle is None

    # GIVEN a sample sheet that exists

    # WHEN including sample sheet to Housekeeper
    transfer_flow_cell_api._include_sample_sheet_to_housekeeper(
        flow_cell_dir=sample_sheet_path.parent, flow_cell_id=flow_cell_id, store=True
    )

    # THEN the sample sheet should be included to Housekeeper
    hk_bundle = transfer_flow_cell_api.hk.bundle(name=SequencingFileTag.SAMPLE_SHEET)
    for hk_file in hk_bundle.versions[0].files:
        assert hk_file.path.endswith("csv")


def test_include_cgstats_log_to_housekeeper_when_not_existing(
    flow_cell_id: str,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
):
    """Test including cgstats log to Housekeeper when not existing."""
    # GIVEN transfer flow cell API

    # GIVEN a cgstats log tag in Housekeeper
    transfer_flow_cell_api._add_tags_to_housekeeper(
        store=True, tags=[SequencingFileTag.CGSTATS_LOG]
    )

    # GIVEN no flow cell id bundle in housekeeper
    hk_bundle = transfer_flow_cell_api.hk.bundle(name=SequencingFileTag.CGSTATS_LOG)
    assert hk_bundle is None

    # GIVEN no cgstats log file

    # WHEN including cgstats log file to Housekeeper
    transfer_flow_cell_api._include_cgstats_log_to_housekeeper(
        flow_cell_dir=Path("does_not_exist"), flow_cell_id=flow_cell_id, store=True
    )

    # THEN the cgstats log file not be included to Housekeeper
    hk_bundle = transfer_flow_cell_api.hk.bundle(name=SequencingFileTag.CGSTATS_LOG)
    assert hk_bundle is None


def test_include_cgstats_log_to_housekeeper(
    flow_cell_id: str,
    cgstats_log_path: Generator[Path, None, None],
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
):
    """Test including cgstats log to Housekeeper."""
    # GIVEN transfer flow cell API

    # GIVEN a cgstats log tag in Housekeeper
    transfer_flow_cell_api._add_tags_to_housekeeper(
        store=True, tags=[SequencingFileTag.CGSTATS_LOG]
    )

    # GIVEN no flow cell id bundle in housekeeper
    hk_bundle = transfer_flow_cell_api.hk.bundle(name=SequencingFileTag.CGSTATS_LOG)
    assert hk_bundle is None

    # GIVEN a cgstats log file that exists

    # WHEN including cgstats log file to Housekeeper
    transfer_flow_cell_api._include_cgstats_log_to_housekeeper(
        flow_cell_dir=cgstats_log_path.parent, flow_cell_id=flow_cell_id, store=True
    )

    # THEN the cgstats log file be included to Housekeeper
    hk_bundle = transfer_flow_cell_api.hk.bundle(name=SequencingFileTag.CGSTATS_LOG)
    for hk_file in hk_bundle.versions[0].files:
        assert hk_file.path.endswith("txt")


def test_store_sequencing_files(
    caplog,
    sample_sheet_path: Generator[Path, None, None],
    flow_cell_id: str,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
):
    """Test storing sequencing files to Housekeeper."""
    caplog.set_level(logging.INFO)
    # GIVEN transfer flow cell API

    # GIVEN a sample sheet tag in Housekeeper
    transfer_flow_cell_api._add_tags_to_housekeeper(
        store=True, tags=[SequencingFileTag.SAMPLE_SHEET]
    )

    # GIVEN no flow cell id bundle in housekeeper
    hk_bundle = transfer_flow_cell_api.hk.bundle(name=SequencingFileTag.SAMPLE_SHEET)
    assert hk_bundle is None

    # GIVEN a sample sheet that exists

    # WHEN adding sample sheet to Housekeeper
    transfer_flow_cell_api._store_sequencing_files(
        flow_cell_id=flow_cell_id,
        sequencing_files=[sample_sheet_path.as_posix()],
        tag_name=SequencingFileTag.SAMPLE_SHEET,
    )

    # THEN we should log that we are adding a file
    assert f"Adding file using tag: {SequencingFileTag.SAMPLE_SHEET}" in caplog.text

    # THEN tha sample sheet should be added to Housekeeper
    hk_bundle = transfer_flow_cell_api.hk.bundle(name=SequencingFileTag.SAMPLE_SHEET)
    for hk_file in hk_bundle.versions[0].files:
        assert hk_file.path.endswith("csv")


def test_include_sequencing_file(
    caplog,
    flow_cell_id: str,
    sample_sheet_path: Generator[Path, None, None],
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
):
    """Test including sequencing files to Housekeeper."""
    caplog.set_level(logging.INFO)
    # GIVEN transfer flow cell API

    # GIVEN a sample sheet tag in Housekeeper
    transfer_flow_cell_api._add_tags_to_housekeeper(
        store=True, tags=[SequencingFileTag.SAMPLE_SHEET]
    )

    # GIVEN no flow cell id bundle in housekeeper
    hk_bundle = transfer_flow_cell_api.hk.bundle(name=SequencingFileTag.SAMPLE_SHEET)
    assert hk_bundle is None

    # GIVEN a sample sheet that exists

    # WHEN adding sample sheet to Housekeeper
    transfer_flow_cell_api._store_sequencing_files(
        flow_cell_id=flow_cell_id,
        sequencing_files=[sample_sheet_path.as_posix()],
        tag_name=SequencingFileTag.SAMPLE_SHEET,
    )

    # THEN we should log that we are adding a file
    assert f"Adding file using tag: {SequencingFileTag.SAMPLE_SHEET}" in caplog.text

    # THEN tha sample sheet should be added to Housekeeper
    hk_bundle = transfer_flow_cell_api.hk.bundle(name=SequencingFileTag.SAMPLE_SHEET)
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


def test_log_enough_reads_when_enough_reads(caplog, sample_name: str):
    """Test logging enough reads."""
    caplog.set_level(logging.INFO)

    # GIVEN a status db sample reads with enough reads

    # GIVEN a sample application expected reads

    # WHEN setting sequenced at for the sample
    log_enough_reads(
        status_db_sample_reads=2, application_expected_reads=1, cgstats_sample_name=sample_name
    )

    # THEN we should log DONE
    assert f"[DONE]" in caplog.text


def test_log_enough_reads_when_not_enough_reads(caplog, sample_name: str):
    """Test logging not enough reads."""
    caplog.set_level(logging.INFO)

    # GIVEN a status db sample with not enough reads

    # GIVEN a sample application expected reads

    # WHEN setting sequenced at for the sample
    log_enough_reads(
        status_db_sample_reads=1, application_expected_reads=2, cgstats_sample_name=sample_name
    )

    # THEN the should log NOT DONE
    assert f"[NOT DONE]" in caplog.text


def test_parse_flow_cell_samples(
    flowcell_store: Store,
    helpers: StoreHelpers,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
    yet_another_flow_cell_id: str,
):
    """Test parsing of flow cell samples."""

    # GIVEN a cgstats flow cell
    cgstats_flow_cell: StatsFlowcell = transfer_flow_cell_api.stats.flowcell(
        yet_another_flow_cell_id
    )

    # GIVEN a flow cell that exist in status db
    flow_cell: Flowcell = helpers.add_flowcell(
        store=flowcell_store, flow_cell_id=yet_another_flow_cell_id
    )

    # GIVEN no sample in flow cell
    assert len(flow_cell.samples) == 0

    # WHEN parsing the flow cell samples
    transfer_flow_cell_api._parse_flow_cell_samples(
        cgstats_flow_cell=cgstats_flow_cell,
        flow_cell=flow_cell,
        flow_cell_id=yet_another_flow_cell_id,
        store=True,
    )

    # THEN a sample should have been added
    assert len(flow_cell.samples) == 1


def test_parse_flow_cell_samples_when_no_cgstats_sample(
    caplog,
    flowcell_store: Store,
    helpers: StoreHelpers,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
    yet_another_flow_cell_id: str,
):
    """Test parsing of flow cell samples when no cgstats sample."""

    # GIVEN a cgstats flow cell
    cgstats_flow_cell: StatsFlowcell = transfer_flow_cell_api.stats.flowcell(
        yet_another_flow_cell_id
    )

    # GIVEN a sample name that does not exist in cgstats
    cgstats_flow_cell.samples[0].name = "sample_does_not_exist_in_cgstats"

    # GIVEN a flow cell that exist in status db
    flow_cell: Flowcell = helpers.add_flowcell(
        store=flowcell_store, flow_cell_id=yet_another_flow_cell_id
    )

    # GIVEN no sample in flow cell
    assert len(flow_cell.samples) == 0

    # WHEN parsing the flow cell samples
    transfer_flow_cell_api._parse_flow_cell_samples(
        cgstats_flow_cell=cgstats_flow_cell,
        flow_cell=flow_cell,
        flow_cell_id=yet_another_flow_cell_id,
        store=True,
    )

    # THEN no sample should have been added
    assert len(flow_cell.samples) == 0

    # THEN we should llog that sample cannot be found
    assert f"Unable to find sample: {cgstats_flow_cell.samples[0].name}" in caplog.text


def test_transfer(
    bcl2fastq_demux_results: DemuxResults,
    flowcell_store: Store,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
    yet_another_flow_cell_id: str,
):
    """Test transfer of sequencing files."""

    # GIVEN a store with a received but not sequenced sample
    housekeeper_api: HousekeeperAPI = transfer_flow_cell_api.hk
    assert flowcell_store.samples().count() == 2
    assert flowcell_store.get_flow_cells().count() == 0
    assert housekeeper_api.bundles().count() == 0

    # GIVEN a sample sheet

    # WHEN transferring the flowcell containing the sample
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        flow_cell = transfer_flow_cell_api.transfer(
            flow_cell_dir=bcl2fastq_demux_results.flow_cell.path,
            flow_cell_id=yet_another_flow_cell_id,
        )

    # THEN it should create a new flow cell record
    assert flowcell_store.get_flow_cells().count() == 1
    assert flow_cell.status == FlowCellStatus.ON_DISK
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

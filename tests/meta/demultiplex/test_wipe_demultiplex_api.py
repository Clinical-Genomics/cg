import logging

from pathlib import Path
from typing import List, Optional

from cg.apps.cgstats.db import models
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.demultiplex.wipe_demultiplex_api import WipeDemuxAPI
from cg.models.cg_config import CGConfig
from cg.store.api import Store
from cg.store.models import Sample, Flowcell
from tests.store_helpers import StoreHelpers


def test_initiate_wipe_demux_api(
    caplog,
    cg_context: CGConfig,
    demultiplexed_flowcells_working_directory: Path,
    flowcell_full_name: str,
):
    """Test to initialize the WipeDemuxAPI"""

    caplog.set_level(logging.DEBUG)

    # GIVEN a correct config
    config = cg_context

    # WHEN initializing the WipeDemuxAPI
    WipeDemuxAPI(
        config=config,
        demultiplexing_dir=demultiplexed_flowcells_working_directory,
        run_name=flowcell_full_name,
    )

    # THEN the API should be correctly initialized
    assert "WipeDemuxAPI: API initiated" in caplog.text


def test_flow_cell_name(wipe_demultiplex_api: WipeDemuxAPI, flow_cell_name: str):
    """Test to parse the correct flow cell name from the run name"""

    # GIVEN a WipeDemuxAPI object with loaded flow cell information
    name_to_be_generated: str = wipe_demultiplex_api.run_name.name.split("_")[-1][1:]

    # WHEN the name is generated
    generated_flow_cell_name = wipe_demultiplex_api.flow_cell_name

    # THEN the parsed name should match the name to be generated
    assert name_to_be_generated == generated_flow_cell_name


def test_get_presence_status_status_db(
    caplog,
    helpers: StoreHelpers,
    wipe_demultiplex_api: WipeDemuxAPI,
    flow_cell_name: str,
):
    """Test to see if the presence of a flowcell is detected in status-db"""
    caplog.set_level(logging.INFO)
    # GIVEN WipeDemuxAPI objects, one with amd one without a flowcell in status-db
    wipe_demux_api: WipeDemuxAPI = wipe_demultiplex_api

    # WHEN the flowcell name is parsed and fetched fetching the presence of a flowcell in either context
    empty_presence: bool = wipe_demux_api.status_db_presence

    # THEN there should be an appropriate presence in both cases
    assert empty_presence is False

    # WHEN adding a flowcell into the statusdb and checking its updated presence
    helpers.add_flowcell(
        store=wipe_demux_api.status_db, flowcell_id=flow_cell_name, sequencer_type="novaseq"
    )
    populated_presence: bool = wipe_demux_api.status_db_presence

    # THEN the presence should be updated
    assert populated_presence is True


def test_set_dry_run_wipe_demux_api(caplog, wipe_demultiplex_api: WipeDemuxAPI):
    """Test to test function to set the API to run in dry run mode"""

    caplog.set_level(logging.DEBUG)

    # GIVEN a dry run flag
    dry_run: bool = True

    # WHEN setting the dry_run mode on a WipeDemuxAPI
    wipe_demultiplex_api.set_dry_run(dry_run=dry_run)

    # THEN the dry run parameter should be set to True and it should be logged
    assert wipe_demultiplex_api.dry_run
    assert f"WipeDemuxAPI: Setting dry run mode to {dry_run}" in caplog.text


def test_no_active_samples_on_flow_cell(
    populated_wipe_demultiplex_api: WipeDemuxAPI, flow_cell_name: str
):
    """Test if the function to find no active samples works correctly"""

    # GIVEN a flowcell with no active samples related to it
    store_: Store = populated_wipe_demultiplex_api.status_db
    samples_on_flow_cell: List[Sample] = (
        store_.query(Flowcell).filter(Flowcell.name == flow_cell_name).first().samples
    )
    assert samples_on_flow_cell
    for sample in samples_on_flow_cell:
        active: bool = store_.active_sample(internal_id=sample.internal_id)
        assert active is False

    # WHEN checking for active samples on flowcell
    populated_wipe_demultiplex_api._set_samples_on_flow_cell()
    active_samples_on_flow_cell: Optional[
        List[str]
    ] = populated_wipe_demultiplex_api.active_samples_on_flow_cell()

    # THEN the no samples on the flowcell should be found active
    assert not active_samples_on_flow_cell


def test_active_samples_on_flow_cell(
    active_flow_cell_store: Store,
    sample_id: str,
    flow_cell_name: str,
    active_wipe_demultiplex_api: WipeDemuxAPI,
):
    """Test if the function to find active samples works correctly"""
    # GIVEN a flowcell with active samples related to it
    store_: Store = active_flow_cell_store

    samples_on_flow_cell: List[Sample] = (
        store_.query(Flowcell).filter(Flowcell.name == flow_cell_name).first().samples
    )

    assert samples_on_flow_cell
    for sample in samples_on_flow_cell:
        active: bool = store_.active_sample(internal_id=sample.internal_id)
        assert active is True

    # WHEN checking for active samples on flowcell
    active_wipe_demultiplex_api._set_samples_on_flow_cell()
    active_samples_on_flow_cell: Optional[
        List[str]
    ] = active_wipe_demultiplex_api.active_samples_on_flow_cell()

    # THEN there should be active samples found
    assert sample_id in active_samples_on_flow_cell


def test_wipe_flow_cell_housekeeper_only_sample_level(
    caplog,
    cg_context: CGConfig,
    demultiplexed_flowcells_working_directory: Path,
    flowcell_full_name: str,
    populated_flow_cell_store: Store,
    sample_level_housekeeper_api: HousekeeperAPI,
    tmp_fastq_paths: List[Path],
):
    """Test function to remove fastqs from Housekeeper when there are only files on sample level
    (not on flow cell name)
    """

    caplog.set_level(logging.INFO)
    cg_context.housekeeper_api_ = sample_level_housekeeper_api
    cg_context.status_db_ = populated_flow_cell_store

    # GIVEN a WipeDemuxAPI with a HousekeeperAPI with no files with flow cell name as a tag

    sample_level_files: List[Path] = tmp_fastq_paths

    wipe_demultiplex_api: WipeDemuxAPI = WipeDemuxAPI(
        config=cg_context,
        demultiplexing_dir=demultiplexed_flowcells_working_directory,
        run_name=flowcell_full_name,
    )
    wipe_demultiplex_api._set_samples_on_flow_cell()
    wipe_demultiplex_api.set_dry_run(dry_run=False)

    # WHEN wiping files in Housekeeper

    wipe_demultiplex_api.wipe_flow_cell_housekeeper()

    # THEN you should be notified that there are no files on flow cell names

    assert (
        f"Housekeeper: No files found with tag: {wipe_demultiplex_api.flow_cell_name}"
        in caplog.text
    )

    # AND you should be notified that there were fastq files removed on sample level

    for file in sample_level_files:
        assert f"{file.as_posix()} deleted" in caplog.text


def test_wipe_flow_cell_housekeeper_flow_cell_name(
    caplog,
    cg_context: CGConfig,
    demultiplexed_flowcells_working_directory: Path,
    flow_cell_name_housekeeper_api: HousekeeperAPI,
    flowcell_full_name: str,
    populated_flow_cell_store: Store,
    tmp_fastq_paths: List[Path],
    tmp_sample_sheet_path: Path,
):
    """Test function to remove files from Housekeeper using flow cell name as a tag"""

    caplog.set_level(logging.INFO)
    cg_context.housekeeper_api_ = flow_cell_name_housekeeper_api
    cg_context.status_db_ = populated_flow_cell_store

    # GIVEN

    fastq_files: List[Path] = tmp_fastq_paths
    sample_sheet_file: Path = tmp_sample_sheet_path

    wipe_demultiplex_api: WipeDemuxAPI = WipeDemuxAPI(
        config=cg_context,
        demultiplexing_dir=demultiplexed_flowcells_working_directory,
        run_name=flowcell_full_name,
    )
    wipe_demultiplex_api._set_samples_on_flow_cell()
    wipe_demultiplex_api.set_dry_run(dry_run=False)

    # WHEN

    wipe_demultiplex_api.wipe_flow_cell_housekeeper()

    # THEN

    assert (
        f"Housekeeper: No files found with tag: {wipe_demultiplex_api.flow_cell_name}"
        not in caplog.text
    )
    assert f"Wiped {sample_sheet_file.as_posix()} from housekeeper" in caplog.text
    for fastq_file in fastq_files:
        assert f"{fastq_file.as_posix()} deleted" in caplog.text


def test_wipe_flow_cell_statusdb(
    caplog,
    flow_cell_name: str,
    populated_wipe_demultiplex_api: WipeDemuxAPI,
    populated_wipe_demux_context: CGConfig,
):
    """Test if function to remove flow cell objects from status db is working"""

    caplog.set_level(logging.INFO)

    # GIVEN a context, with a status db filled with a flow cell object

    wipe_demux_api: WipeDemuxAPI = populated_wipe_demultiplex_api
    wipe_demux_api.set_dry_run(dry_run=False)

    existing_object: Flowcell = (
        populated_wipe_demux_context.status_db.query(Flowcell)
        .filter(Flowcell.name == flow_cell_name)
        .first()
    )
    assert existing_object

    # WHEN removing the object from the database

    wipe_demux_api.wipe_flow_cell_statusdb()

    # THEN the user should be informed that the object was removed

    assert f"StatusDB: Wiping flowcell {wipe_demux_api.flow_cell_name}" in caplog.text

    # AND the object should no longer exist in status db

    existing_object: Flowcell = (
        populated_wipe_demux_context.status_db.query(Flowcell)
        .filter(Flowcell.name == flow_cell_name)
        .first()
    )

    assert not existing_object


def test_wipe_flow_cell_demultiplex_dir(
    caplog, populated_wipe_demultiplex_api: WipeDemuxAPI, tmp_demulitplexing_dir: Path
):
    """Test if function to remove files from the file system is working"""

    caplog.set_level(logging.INFO)
    wipe_demux_api: WipeDemuxAPI = populated_wipe_demultiplex_api
    wipe_demux_api.set_dry_run(dry_run=False)

    # GIVEN an existing demultiplexed-runs directory of a run

    assert tmp_demulitplexing_dir.exists()

    # WHEN removing said files with the WipeDemuxAPI

    wipe_demux_api.wipe_flow_cell_demultiplex_dir()

    assert f"Hasta: Removing flow cell directory {tmp_demulitplexing_dir.as_posix()}" in caplog.text
    assert tmp_demulitplexing_dir.exists() is False


def test_wipe_flow_cell_cgstats(
    caplog,
    populated_wipe_demux_context: CGConfig,
    populated_wipe_demultiplex_api: WipeDemuxAPI,
    flow_cell_name: str,
):
    """Test if function to remove objects from cg-stats is working"""

    caplog.set_level(logging.INFO)
    wipe_demux_api: WipeDemuxAPI = populated_wipe_demultiplex_api
    wipe_demux_api.set_dry_run(dry_run=False)

    # GIVEN an existing object in cg-stags database

    existing_object: models.Flowcell = (
        populated_wipe_demux_context.cg_stats_api.query(models.Flowcell)
        .filter(models.Flowcell.flowcellname == flow_cell_name)
        .first()
    )

    assert existing_object

    # WHEN wiping the existance of said object

    wipe_demux_api.wipe_flow_cell_cgstats()

    # THEN the user should be notified that the object was removed

    assert f"Removing entry {flow_cell_name} in from cgstats" in caplog.text

    # AND the object should no longer exist

    existing_object: models.Flowcell = (
        populated_wipe_demux_context.cg_stats_api.query(models.Flowcell)
        .filter(models.Flowcell.flowcellname == flow_cell_name)
        .first()
    )

    assert not existing_object

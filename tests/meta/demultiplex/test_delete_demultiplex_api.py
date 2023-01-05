import logging
import pytest

from pathlib import Path
from typing import List, Optional

from cg.apps.cgstats.db import models
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import DeleteDemuxError
from cg.meta.demultiplex.delete_demultiplex_api import DeleteDemuxAPI
from cg.models.cg_config import CGConfig
from cg.store.api import Store
from cg.store.models import Sample, Flowcell
from tests.store_helpers import StoreHelpers


def test_initiate_delete_demux_api(
    caplog,
    cg_context: CGConfig,
    demultiplexed_flow_cells_working_directory: Path,
    flow_cell_full_name: str,
):
    """Test to initialize the DeleteDemuxAPI"""

    caplog.set_level(logging.DEBUG)

    # GIVEN a correct config
    config = cg_context

    # WHEN initializing the DeleteDemuxAPI
    DeleteDemuxAPI(
        config=config,
        demultiplex_base=demultiplexed_flow_cells_working_directory,
        dry_run=True,
        run_path=flow_cell_full_name,
    )

    # THEN the API should be correctly initialized
    assert "DeleteDemuxAPI: API initiated" in caplog.text


def test_flowcell_name(wipe_demultiplex_api: DeleteDemuxAPI, flow_cell_id: str):
    """Test to parse the correct flow cell name from the run name."""

    # GIVEN a DeleteDemuxAPI object with loaded flow cell information
    name_to_be_generated: str = flow_cell_id

    # WHEN the name is generated
    generated_flow_cell_name = wipe_demultiplex_api.flow_cell_name

    # THEN the parsed name should match the name to be generated
    assert name_to_be_generated == generated_flow_cell_name


def test_get_presence_status_status_db(
    caplog,
    helpers: StoreHelpers,
    wipe_demultiplex_api: DeleteDemuxAPI,
    flow_cell_id: str,
):
    """Test to see if the presence of a flow cell is detected in status-db."""
    caplog.set_level(logging.INFO)
    # GIVEN DeleteDemuxAPI objects, one with amd one without a flowcell in status-db
    wipe_demux_api: DeleteDemuxAPI = wipe_demultiplex_api

    # WHEN the flowcell name is parsed and fetched fetching the presence of a flowcell in either context
    empty_presence: bool = wipe_demux_api.status_db_presence

    # THEN there should be an appropriate presence in both cases
    assert not empty_presence

    # WHEN adding a flowcell into the statusdb and checking its updated presence
    helpers.add_flowcell(
        store=wipe_demux_api.status_db, flow_cell_id=flow_cell_id, sequencer_type="novaseq"
    )
    populated_presence: bool = wipe_demux_api.status_db_presence

    # THEN the presence should be updated
    assert populated_presence


def test_set_dry_run_delete_demux_api(
    caplog,
    cg_context: CGConfig,
    demultiplexed_flow_cells_working_directory: Path,
    flow_cell_full_name: str,
    stats_api: StatsAPI,
):
    """Test to test function to set the API to run in dry run mode"""

    caplog.set_level(logging.DEBUG)
    cg_context.cg_stats_api_ = stats_api
    # WHEN setting the dry_run mode on a DeleteDemuxAPI
    wipe_demultiplex_api: DeleteDemuxAPI = DeleteDemuxAPI(
        config=cg_context,
        demultiplex_base=demultiplexed_flow_cells_working_directory,
        dry_run=True,
        run_path=flow_cell_full_name,
    )

    # THEN the dry run parameter should be set to True and it should be logged
    assert wipe_demultiplex_api.dry_run
    assert f"DeleteDemuxAPI: Setting dry run mode to True" in caplog.text


def test_no_active_samples_on_flow_cell(
    populated_wipe_demultiplex_api: DeleteDemuxAPI, flow_cell_id: str
):
    """Test if the function to find no active samples works correctly"""

    # GIVEN a flow cell with no active samples related to it
    store_: Store = populated_wipe_demultiplex_api.status_db
    samples_on_flow_cell: List[Sample] = (
        store_.query(Flowcell).filter(Flowcell.name == flow_cell_id).first().samples
    )
    assert samples_on_flow_cell
    for sample in samples_on_flow_cell:
        active: bool = store_.active_sample(internal_id=sample.internal_id)
        assert not active

    # WHEN checking for active samples on flowcell
    populated_wipe_demultiplex_api._set_samples_on_flow_cell()
    active_samples_on_flow_cell: Optional[
        List[str]
    ] = populated_wipe_demultiplex_api.active_samples_on_flow_cell()

    # THEN the no samples on the flowcell should be found active
    assert not active_samples_on_flow_cell


def test_active_samples_on_flow_cell(
    active_flow_cell_store: Store,
    flow_cell_id: str,
    active_wipe_demultiplex_api: DeleteDemuxAPI,
):
    """Test if the function to find active samples works correctly"""
    # GIVEN a flow cell with active samples related to it
    store_: Store = active_flow_cell_store

    samples_on_flow_cell: List[Sample] = (
        store_.query(Flowcell).filter(Flowcell.name == flow_cell_id).first().samples
    )

    assert samples_on_flow_cell
    for sample in samples_on_flow_cell:
        active: bool = store_.active_sample(internal_id=sample.internal_id)
        assert active

    # WHEN checking for active samples on flowcell
    active_wipe_demultiplex_api._set_samples_on_flow_cell()
    active_samples_on_flow_cell: Optional[
        List[str]
    ] = active_wipe_demultiplex_api.active_samples_on_flow_cell()

    # THEN there should be active samples found
    assert any(sample.internal_id in active_samples_on_flow_cell for sample in samples_on_flow_cell)


def test_check_active_sample(active_wipe_demultiplex_api: DeleteDemuxAPI):
    """Test that proper exception is raised when active samples are identified"""

    # GIVEN a DeleteDemuxAPI and a store with active samples related to it

    wipe_demux_api: DeleteDemuxAPI = active_wipe_demultiplex_api
    wipe_demux_api.set_dry_run(dry_run=False)

    # WHEN checking if there are active samples on flowcell to be deleted

    with pytest.raises(DeleteDemuxError):
        # THEN the proper error should be raised
        wipe_demux_api.check_active_samples()


def test_delete_flow_cell_housekeeper_only_sample_level(
    caplog,
    cg_context: CGConfig,
    demultiplexed_flow_cells_working_directory: Path,
    flow_cell_full_name: str,
    populated_flow_cell_store: Store,
    sample_level_housekeeper_api: HousekeeperAPI,
):
    """Test removing fastqs from Housekeeper when there are only files on sample level
    (not on flow cell name).
    """

    caplog.set_level(logging.INFO)
    cg_context.housekeeper_api_ = sample_level_housekeeper_api
    cg_context.status_db_ = populated_flow_cell_store

    # GIVEN a DeleteDemuxAPI with a HousekeeperAPI with no files with flow cell name as a tag

    wipe_demultiplex_api: DeleteDemuxAPI = DeleteDemuxAPI(
        config=cg_context,
        demultiplex_base=demultiplexed_flow_cells_working_directory,
        dry_run=False,
        run_path=Path(flow_cell_full_name),
    )
    wipe_demultiplex_api._set_samples_on_flow_cell()

    # WHEN wiping files in Housekeeper

    wipe_demultiplex_api.delete_flow_cell_housekeeper()

    # THEN you should be notified that there are no files on flow cell names

    assert (
        f"Housekeeper: No files found with tag: {wipe_demultiplex_api.flow_cell_name}"
        in caplog.text
    )

    # THEN you should be notified that there were fastq files removed on sample level
    assert "Deleting file" in caplog.text


def test_delete_flow_cell_housekeeper_flowcell_name(
    caplog,
    cg_context: CGConfig,
    demultiplexed_flow_cells_working_directory: Path,
    flow_cell_name_housekeeper_api: HousekeeperAPI,
    flow_cell_full_name: str,
    populated_flow_cell_store: Store,
    tmp_sample_sheet_path: Path,
):
    """Test removing files from Housekeeper using flow cell name as a tag."""

    caplog.set_level(logging.INFO)
    cg_context.housekeeper_api_ = flow_cell_name_housekeeper_api
    cg_context.status_db_ = populated_flow_cell_store

    # GIVEN

    sample_sheet_file: Path = tmp_sample_sheet_path

    wipe_demultiplex_api: DeleteDemuxAPI = DeleteDemuxAPI(
        config=cg_context,
        demultiplex_base=demultiplexed_flow_cells_working_directory,
        dry_run=False,
        run_path=Path(flow_cell_full_name),
    )
    wipe_demultiplex_api._set_samples_on_flow_cell()

    # WHEN

    wipe_demultiplex_api.delete_flow_cell_housekeeper()

    # THEN

    assert (
        f"Housekeeper: No files found with tag: {wipe_demultiplex_api.flow_cell_name}"
        not in caplog.text
    )
    assert f"Deleted {sample_sheet_file.as_posix()} from housekeeper" in caplog.text

    # THEN you should be notified that there were fastq files removed on sample level
    assert "Deleting file" in caplog.text


def test_delete_flow_cell_statusdb(
    caplog,
    flow_cell_id: str,
    populated_wipe_demultiplex_api: DeleteDemuxAPI,
    populated_wipe_demux_context: CGConfig,
):
    """Test if function to remove flow cell objects from status db is working"""

    caplog.set_level(logging.INFO)

    # GIVEN a context, with a status db filled with a flow cell object

    wipe_demux_api: DeleteDemuxAPI = populated_wipe_demultiplex_api
    wipe_demux_api.set_dry_run(dry_run=False)

    existing_object: Flowcell = (
        populated_wipe_demux_context.status_db.query(Flowcell)
        .filter(Flowcell.name == flow_cell_id)
        .first()
    )
    assert existing_object

    # WHEN removing the object from the database

    wipe_demux_api.delete_flow_cell_statusdb()

    # THEN the user should be informed that the object was removed

    assert f"StatusDB: Deleted flowcell {wipe_demux_api.flow_cell_name}" in caplog.text

    # AND the object should no longer exist in status db

    existing_object: Flowcell = (
        populated_wipe_demux_context.status_db.query(Flowcell)
        .filter(Flowcell.name == flow_cell_id)
        .first()
    )

    assert not existing_object


def test_delete_flow_cell_hasta(
    caplog,
    populated_wipe_demultiplex_api: DeleteDemuxAPI,
    tmp_demulitplexing_dir: Path,
    tmp_flow_cell_run_path: Path,
):
    """Test if function to remove files from the file system is working"""

    caplog.set_level(logging.INFO)
    wipe_demux_api: DeleteDemuxAPI = populated_wipe_demultiplex_api
    flow_cell_obj: Flowcell = wipe_demux_api.status_db.get_flow_cell(wipe_demux_api.flow_cell_name)
    wipe_demux_api.set_dry_run(dry_run=False)

    # GIVEN an existing demultiplexing and run directory of a flow cell, with a status "ondisk"

    assert tmp_demulitplexing_dir.exists()
    assert tmp_flow_cell_run_path.exists()
    assert flow_cell_obj.status == "ondisk"

    # WHEN removing said files with the DeleteDemuxAPI

    wipe_demux_api.delete_flow_cell_hasta(
        demultiplexing_dir=True,
        run_dir=True,
    )

    # THEN the demultiplexing directory should be removed
    assert (
        f"DeleteDemuxAPI-Hasta: Removing flow cell demultiplexing directory: {tmp_demulitplexing_dir.as_posix()}"
        in caplog.text
    )
    assert tmp_demulitplexing_dir.exists() is False

    # THEN the run directory should be removed
    assert (
        f"DeleteDemuxAPI-Hasta: Removing flow cell run directory: {tmp_flow_cell_run_path.as_posix()}"
        in caplog.text
    )
    assert tmp_flow_cell_run_path.exists() is False

    # THEN the status of the flow cell in statusdb should be set to removed
    assert flow_cell_obj.status == "removed"


def test_delete_flow_cell_cgstats(
    caplog,
    populated_wipe_demux_context: CGConfig,
    populated_wipe_demultiplex_api: DeleteDemuxAPI,
    flow_cell_id: str,
):
    """Test if function to remove objects from cg-stats is working"""

    caplog.set_level(logging.INFO)
    wipe_demux_api: DeleteDemuxAPI = populated_wipe_demultiplex_api
    wipe_demux_api.set_dry_run(dry_run=False)

    # GIVEN an existing object in cg-stags database

    existing_object: models.Flowcell = (
        populated_wipe_demux_context.cg_stats_api.query(models.Flowcell)
        .filter(models.Flowcell.flowcellname == flow_cell_id)
        .first()
    )

    assert existing_object

    # WHEN wiping the existance of said object

    wipe_demux_api.delete_flow_cell_cgstats()

    # THEN the user should be notified that the object was removed

    assert f"Removing entry {flow_cell_id} in from cgstats" in caplog.text

    # AND the object should no longer exist

    existing_object: models.Flowcell = (
        populated_wipe_demux_context.cg_stats_api.query(models.Flowcell)
        .filter(models.Flowcell.flowcellname == flow_cell_id)
        .first()
    )

    assert not existing_object


def test_delete_demultiplexing_init_files(
    caplog, demultiplexing_init_files: List[Path], populated_wipe_demultiplex_api: DeleteDemuxAPI
):
    """Test function to remove demultiplexing init files from the filesystem"""

    # GIVEN a list of paths to existing demultiplexing init filesystem and a initiated DeleteDemuxAPI
    wipe_demux_api = populated_wipe_demultiplex_api
    wipe_demux_api.set_dry_run(dry_run=False)

    assert all(init_file.exists() for init_file in demultiplexing_init_files)

    # WHEN wiping the existance of mentioned files

    wipe_demux_api.delete_demux_init_files()

    # THEN the files should no longer exist

    assert not any(init_file.exists() for init_file in demultiplexing_init_files)

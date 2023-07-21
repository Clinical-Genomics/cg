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
    flow_cell_name: str,
    tmp_flow_cell_run_base_path: Path,
    bcl2fastq_flow_cell_id: str,
):
    """Test to initialize the DeleteDemuxAPI"""

    caplog.set_level(logging.DEBUG)

    # GIVEN a correct config
    config = cg_context
    config.demultiplex_api.run_dir = tmp_flow_cell_run_base_path
    config.demultiplex_api.out_dir = tmp_flow_cell_run_base_path
    Path(tmp_flow_cell_run_base_path, f"some_prefix_1100_{bcl2fastq_flow_cell_id}").mkdir(
        parents=True, exist_ok=True
    )
    # WHEN initializing the DeleteDemuxAPI
    DeleteDemuxAPI(
        config=config,
        flow_cell_name=bcl2fastq_flow_cell_id,
        dry_run=True,
    )

    # THEN the API should be correctly initialized
    assert "DeleteDemuxAPI: API initiated" in caplog.text


def test_get_presence_status_status_db(
    caplog,
    helpers: StoreHelpers,
    delete_demultiplex_api: DeleteDemuxAPI,
    bcl2fastq_flow_cell_id: str,
):
    """Test to see if the presence of a flow cell is detected in status-db."""
    caplog.set_level(logging.INFO)
    # GIVEN DeleteDemuxAPI objects, one with amd one without a flowcell in status-db
    delete_demux_api: DeleteDemuxAPI = delete_demultiplex_api

    # WHEN the flowcell name is parsed and fetching the presence of a flowcell in either context
    empty_presence: bool = delete_demux_api.status_db_presence

    # THEN there should be an appropriate presence in both cases
    assert not empty_presence

    # WHEN adding a flowcell into the statusdb and checking its updated presence
    helpers.add_flowcell(
        store=delete_demux_api.status_db,
        flow_cell_name=bcl2fastq_flow_cell_id,
        sequencer_type="novaseq",
    )
    populated_presence: bool = delete_demux_api.status_db_presence

    # THEN the presence should be updated
    assert populated_presence


def test_set_dry_run_delete_demux_api(
    caplog,
    cg_context: CGConfig,
    bcl2fastq_flow_cell_id: str,
    stats_api: StatsAPI,
    tmp_flow_cell_run_base_path: Path,
):
    """Test to test function to set the API to run in dry run mode"""

    caplog.set_level(logging.DEBUG)
    cg_context.cg_stats_api_ = stats_api
    cg_context.demultiplex_api.run_dir = tmp_flow_cell_run_base_path
    cg_context.demultiplex_api.out_dir = tmp_flow_cell_run_base_path
    Path(tmp_flow_cell_run_base_path, f"some_prefix_1100_{bcl2fastq_flow_cell_id}").mkdir(
        parents=True, exist_ok=True
    )
    # WHEN setting the dry_run mode on a DeleteDemuxAPI
    delete_demultiplex_api: DeleteDemuxAPI = DeleteDemuxAPI(
        config=cg_context,
        dry_run=True,
        flow_cell_name=bcl2fastq_flow_cell_id,
    )

    # THEN the dry run parameter should be set to True and it should be logged
    assert delete_demultiplex_api.dry_run
    assert "DeleteDemuxAPI: Setting dry run mode to True" in caplog.text


def test_no_active_samples_on_flow_cell(
    populated_delete_demultiplex_api: DeleteDemuxAPI, bcl2fastq_flow_cell_id: str
):
    """Test if the function to find no active samples works correctly."""

    # GIVEN a flow cell with no active samples related to it
    store: Store = populated_delete_demultiplex_api.status_db
    flow_cell = store.get_flow_cell_by_name(flow_cell_name=bcl2fastq_flow_cell_id)
    samples_on_flow_cell: List[Sample] = flow_cell.samples

    assert samples_on_flow_cell
    for sample in samples_on_flow_cell:
        active: bool = store.has_active_cases_for_sample(internal_id=sample.internal_id)
        assert not active

    # WHEN checking for active samples on flowcell
    populated_delete_demultiplex_api._set_samples_on_flow_cell()
    active_samples_on_flow_cell: Optional[
        List[str]
    ] = populated_delete_demultiplex_api.active_samples_on_flow_cell()

    # THEN the no samples on the flowcell should be found active
    assert not active_samples_on_flow_cell


def test_active_samples_on_flow_cell(
    active_flow_cell_store: Store,
    bcl2fastq_flow_cell_id: str,
    active_delete_demultiplex_api: DeleteDemuxAPI,
):
    """Test if the function to find active samples works correctly."""
    # GIVEN a flow cell with active samples related to it
    store: Store = active_flow_cell_store
    flow_cell = store.get_flow_cell_by_name(flow_cell_name=bcl2fastq_flow_cell_id)
    samples_on_flow_cell: List[Sample] = flow_cell.samples

    assert samples_on_flow_cell
    for sample in samples_on_flow_cell:
        active: bool = store.has_active_cases_for_sample(internal_id=sample.internal_id)
        assert active

    # WHEN checking for active samples on flowcell
    active_delete_demultiplex_api._set_samples_on_flow_cell()
    active_samples_on_flow_cell: Optional[
        List[str]
    ] = active_delete_demultiplex_api.active_samples_on_flow_cell()

    # THEN there should be active samples found
    assert any(sample.internal_id in active_samples_on_flow_cell for sample in samples_on_flow_cell)


def test_check_active_sample(active_delete_demultiplex_api: DeleteDemuxAPI):
    """Test that proper exception is raised when active samples are identified"""

    # GIVEN a DeleteDemuxAPI and a store with active samples related to it

    delete_demux_api: DeleteDemuxAPI = active_delete_demultiplex_api
    delete_demux_api.set_dry_run(dry_run=False)

    # WHEN checking if there are active samples on flowcell to be deleted

    with pytest.raises(DeleteDemuxError):
        # THEN the proper error should be raised
        delete_demux_api.check_active_samples()


def test_delete_flow_cell_housekeeper_only_sample_level(
    caplog,
    cg_context: CGConfig,
    tmp_flow_cell_run_base_path: Path,
    bcl2fastq_flow_cell_id: str,
    populated_flow_cell_store: Store,
    sample_level_housekeeper_api: HousekeeperAPI,
):
    """Test removing fastqs from Housekeeper when there are only files on sample level
    (not on flow cell name).
    """

    caplog.set_level(logging.INFO)

    cg_context.demultiplex_api.run_dir = tmp_flow_cell_run_base_path
    cg_context.demultiplex_api.out_dir = tmp_flow_cell_run_base_path
    Path(tmp_flow_cell_run_base_path, f"some_prefix_1100_{bcl2fastq_flow_cell_id}").mkdir(
        parents=True, exist_ok=True
    )
    # GIVEN a DeleteDemuxAPI with a HousekeeperAPI with no files with flow cell name as a tag

    delete_demultiplex_api: DeleteDemuxAPI = DeleteDemuxAPI(
        config=cg_context,
        dry_run=False,
        flow_cell_name=bcl2fastq_flow_cell_id,
    )
    delete_demultiplex_api.housekeeper_api = sample_level_housekeeper_api
    delete_demultiplex_api._set_samples_on_flow_cell()

    # WHEN wiping files in Housekeeper

    delete_demultiplex_api.delete_flow_cell_housekeeper()

    # THEN you should be notified that there are no files on flow cell names

    assert (
        f"Housekeeper: No files found with tag: {delete_demultiplex_api.flow_cell_name}"
        in caplog.text
    )

    # THEN you should be notified that there were fastq files removed on sample level
    assert "Deleting file" in caplog.text


def test_delete_flow_cell_housekeeper_flowcell_name(
    caplog,
    cg_context: CGConfig,
    tmp_flow_cell_run_base_path: Path,
    tmp_flow_cell_demux_base_path: Path,
    flow_cell_name_housekeeper_api: HousekeeperAPI,
    bcl2fastq_flow_cell_id: str,
    populated_flow_cell_store: Store,
    tmp_sample_sheet_path: Path,
):
    """Test removing files from Housekeeper using flow cell name as a tag."""

    caplog.set_level(logging.INFO)
    cg_context.housekeeper_api_ = flow_cell_name_housekeeper_api
    cg_context.status_db_ = populated_flow_cell_store
    cg_context.demultiplex_api.run_dir = tmp_flow_cell_run_base_path
    cg_context.demultiplex_api.out_dir = tmp_flow_cell_demux_base_path
    Path(tmp_flow_cell_run_base_path, f"some_prefix_1100_{bcl2fastq_flow_cell_id}").mkdir(
        parents=True, exist_ok=True
    )
    Path(tmp_flow_cell_demux_base_path, f"some_prefix_1100_{bcl2fastq_flow_cell_id}").mkdir(
        parents=True, exist_ok=True
    )
    # GIVEN

    sample_sheet_file: Path = tmp_sample_sheet_path

    delete_demultiplex_api: DeleteDemuxAPI = DeleteDemuxAPI(
        config=cg_context,
        dry_run=False,
        flow_cell_name=bcl2fastq_flow_cell_id,
    )
    delete_demultiplex_api.housekeeper_api = flow_cell_name_housekeeper_api
    delete_demultiplex_api._set_samples_on_flow_cell()

    # WHEN

    delete_demultiplex_api.delete_flow_cell_housekeeper()

    # THEN

    assert (
        f"Housekeeper: No files found with tag: {delete_demultiplex_api.flow_cell_name}"
        not in caplog.text
    )
    assert f"Deleted {sample_sheet_file.as_posix()} from housekeeper" in caplog.text

    # THEN you should be notified that there were fastq files removed on sample level
    assert "Deleting file" in caplog.text


def test_delete_flow_cell_statusdb(
    caplog,
    bcl2fastq_flow_cell_id: str,
    populated_delete_demultiplex_api: DeleteDemuxAPI,
    populated_delete_demux_context: CGConfig,
):
    """Test if function to remove flow cell objects from status db is working."""

    caplog.set_level(logging.INFO)

    # GIVEN a context, with a status db filled with a flow cell object
    delete_demux_api: DeleteDemuxAPI = populated_delete_demultiplex_api
    delete_demux_api.set_dry_run(dry_run=False)
    store = populated_delete_demux_context.status_db
    flow_cell: Flowcell = store.get_flow_cell_by_name(flow_cell_name=bcl2fastq_flow_cell_id)
    assert flow_cell

    # WHEN removing the flow cell from the database
    delete_demux_api.delete_flow_cell_in_status_db()

    # THEN the user should be informed that the flow cell was removed
    assert f"StatusDB: Deleted flowcell {delete_demux_api.flow_cell_name}" in caplog.text

    # AND the flow cell should no longer exist in status db
    flow_cell: Flowcell = store.get_flow_cell_by_name(flow_cell_name=bcl2fastq_flow_cell_id)
    assert not flow_cell


def test_delete_flow_cell_hasta(
    caplog,
    populated_delete_demultiplex_api: DeleteDemuxAPI,
):
    """Test if function to remove files from the file system is working"""

    caplog.set_level(logging.INFO)
    delete_demux_api: DeleteDemuxAPI = populated_delete_demultiplex_api

    flow_cell_obj: Flowcell = delete_demux_api.status_db.get_flow_cell_by_name(
        delete_demux_api.flow_cell_name
    )
    delete_demux_api.set_dry_run(dry_run=False)

    # GIVEN an existing demultiplexing and run directory of a flow cell, with a status "ondisk"

    assert delete_demux_api.demultiplexing_out_path.exists()
    assert delete_demux_api.run_path.exists()
    assert flow_cell_obj.status == "ondisk"

    # WHEN removing said files with the DeleteDemuxAPI

    delete_demux_api.delete_flow_cell_hasta(
        demultiplexing_dir=True,
        run_dir=True,
    )

    # THEN the demultiplexing directory should be removed
    assert (
        f"DeleteDemuxAPI-Hasta: Removing flow cell demultiplexing directory: {delete_demux_api.demultiplexing_out_path}"
        in caplog.text
    )
    assert delete_demux_api.demultiplexing_out_path.exists() is False

    # THEN the run directory should be removed
    assert (
        f"DeleteDemuxAPI-Hasta: Removing flow cell run directory: {delete_demux_api.run_path}"
        in caplog.text
    )
    assert delete_demux_api.run_path.exists() is False

    # THEN the status of the flow cell in statusdb should be set to removed
    assert flow_cell_obj.status == "removed"


def test_delete_flow_cell_cgstats(
    caplog,
    populated_delete_demux_context: CGConfig,
    populated_delete_demultiplex_api: DeleteDemuxAPI,
    bcl2fastq_flow_cell_id: str,
):
    """Test if function to remove objects from cg-stats is working."""

    caplog.set_level(logging.INFO)
    delete_demux_api: DeleteDemuxAPI = populated_delete_demultiplex_api
    delete_demux_api.set_dry_run(dry_run=False)

    # GIVEN an existing object in cg-stags database

    existing_object: models.Flowcell = (
        populated_delete_demux_context.cg_stats_api.query(models.Flowcell)
        .filter(models.Flowcell.flowcellname == bcl2fastq_flow_cell_id)
        .first()
    )

    assert existing_object

    # WHEN wiping the existence of said object

    delete_demux_api.delete_flow_cell_cgstats()

    # THEN the user should be notified that the object was removed

    assert f"Removing entry {bcl2fastq_flow_cell_id} in from cgstats" in caplog.text

    # AND the object should no longer exist

    existing_object: models.Flowcell = (
        populated_delete_demux_context.cg_stats_api.query(models.Flowcell)
        .filter(models.Flowcell.flowcellname == bcl2fastq_flow_cell_id)
        .first()
    )

    assert not existing_object


def test_delete_demultiplexing_init_files(
    caplog, demultiplexing_init_files: List[Path], populated_delete_demultiplex_api: DeleteDemuxAPI
):
    """Test function to remove demultiplexing init files from the filesystem"""

    # GIVEN a list of paths to existing demultiplexing init filesystem and a initiated DeleteDemuxAPI
    delete_demux_api = populated_delete_demultiplex_api
    delete_demux_api.set_dry_run(dry_run=False)

    assert all(init_file.exists() for init_file in demultiplexing_init_files)

    # WHEN wiping the existance of mentioned files

    delete_demux_api.delete_demux_init_files()

    # THEN the files should no longer exist

    assert not any(init_file.exists() for init_file in demultiplexing_init_files)


def test_delete_flow_cell_sample_lane_sequencing_metrics(
    caplog,
    populated_sample_lane_sequencing_metrics_demultiplex_api: DeleteDemuxAPI,
    populated_sample_lane_seq_demux_context: CGConfig,
    flow_cell_name: str,
):
    """Test removing objects from sample lane sequencing metrics."""

    caplog.set_level(logging.INFO)

    # GIVEN a delete demultiplex API with a sequencing metric object

    wipe_demux_api: DeleteDemuxAPI = populated_sample_lane_sequencing_metrics_demultiplex_api
    wipe_demux_api.set_dry_run(dry_run=False)
    assert wipe_demux_api.status_db.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell_name
    )

    # WHEN wiping the existence of said object

    wipe_demux_api.delete_flow_cell_sample_lane_sequencing_metrics()

    # THEN the object should not exist anymore and the user should be notified

    assert not wipe_demux_api.status_db.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell_name
    )
    assert (
        f"Delete entries for Flow Cell: {flow_cell_name} in the Sample Lane Sequencing Metrics table"
        in caplog.text
    )

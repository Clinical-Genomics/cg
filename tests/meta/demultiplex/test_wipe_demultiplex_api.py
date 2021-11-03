import logging
from pathlib import Path

from cg.meta.demultiplex.wipe_demultiplex_api import WipeDemuxAPI
from cg.models.cg_config import CGConfig


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


def test_parse_flowcell_name(wipe_demultiplex_api: WipeDemuxAPI, flow_cell_name: str):
    """Test to parse the correct flow cell name from the run name"""

    # GIVEN a WipeDemuxAPI object with loaded flow cell information
    name_to_be_generated: str = wipe_demultiplex_api.run_name.split("_")[-1][1:]

    # WHEN the name is parsed
    wipe_demultiplex_api.parse_flowcell_name()

    # THEN the parsed name should match the name to be generated
    assert name_to_be_generated == wipe_demultiplex_api.flow_cell_name


def test_set_dry_run_wipe_demux_api(caplog, wipe_demultiplex_api: WipeDemuxAPI):
    """Test to test function to set the API to run in dry run mode"""

    caplog.set_level(logging.DEBUG)

    # GIVEN a dry run flag
    dry_run: bool = True

    # WHEN setting the dry_run mode on a WipeDemuxAPI
    wipe_demultiplex_api.set_dry_run(dry_run=dry_run)

    # THEN the dry run parameter should be set to True and it should be logged
    assert wipe_demultiplex_api.dry_run
    assert f"WipeDemuxAPI: Setting dry run mode to: {dry_run}" in caplog.text


def test_get_presence_status_status_db(
    populated_wipe_demultiplex_api: WipeDemuxAPI,
    wipe_demultiplex_api: WipeDemuxAPI,
    flow_cell_name: str,
):
    """Test to see if the presence of a flowcell is detected in status-db"""

    # GIVEN WipeDemuxAPI objects, one with amd one without a flowcell in status-db
    empty_context: WipeDemuxAPI = wipe_demultiplex_api
    populated_context: WipeDemuxAPI = populated_wipe_demultiplex_api

    # WHEN fetching the presence of a flowcell in either context
    empty_presence: bool = empty_context._get_presence_status_status_db()
    populated_presence: bool = populated_context._get_presence_status_status_db()

    # THEN there should be an appropriate presence in both cases
    assert empty_presence is False
    assert populated_presence is True

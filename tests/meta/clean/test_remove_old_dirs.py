import datetime
from pathlib import Path
from typing import Dict

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.clean.flow_cell_run_directories import RunDirFlowCell
from cg.store import Store
from tests.store_helpers import StoreHelpers


def test_archive_flow_cell_run_directory(
    caplog,
    real_housekeeper_api: HousekeeperAPI,
    tmp_flow_cells_directory_ready_for_demultiplexing_bcl2fastq: Path,
    timestamp: datetime.datetime,
    base_store: Store,
    helpers: StoreHelpers,
):
    # GIVEN an old flow cell which is not tagged as archived but whose sample sheet is included in Housekeeper

    bundle_data: Dict = {"name": "HLG5GDRXY", "created": timestamp, "files": []}

    helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=bundle_data)

    real_housekeeper_api.add_and_include_file_to_latest_version(
        bundle_name="HLG5GDRXY",
        file=Path(tmp_flow_cells_directory_ready_for_demultiplexing_bcl2fastq, "SampleSheet.csv"),
        tags=["samplesheet", "HLG5GDRXY"],
    )

    # WHEN running archive_sample_sheet in the run directory
    run_dir_flow_cell: RunDirFlowCell = RunDirFlowCell(
        flow_cell_dir=tmp_flow_cells_directory_ready_for_demultiplexing_bcl2fastq,
        status_db=base_store,
        housekeeper_api=real_housekeeper_api,
    )
    run_dir_flow_cell.archive_sample_sheet()

    # THEN assert the archiving is skipped
    assert "Sample sheet already included!" in caplog.text

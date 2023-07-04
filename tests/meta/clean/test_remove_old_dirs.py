import datetime
from pathlib import Path
from typing import Dict, List

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.clean.flow_cell_run_directories import RunDirFlowCell
from cg.store import Store
from housekeeper.store.models import File, Tag, Version
from tests.store_helpers import StoreHelpers


def test_archive_flow_cell_run_directory(
    caplog,
    real_housekeeper_api: HousekeeperAPI,
    dragen_flow_cell_dir: Path,
    timestamp: datetime.datetime,
    base_store: Store,
    helpers: StoreHelpers,
):
    # GIVEN an old flow cell which is not tagged as archived but whose sample sheet is included in Housekeeper

    bundle_data: Dict = {"name": "HLG5GDRXY", "created": timestamp, "files": []}

    helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=bundle_data)

    real_housekeeper_api.add_and_include_file_to_latest_version(
        bundle_name="HLG5GDRXY",
        file=Path(dragen_flow_cell_dir, "SampleSheet.csv"),
        tags=["samplesheet", "HLG5GDRXY"],
    )

    # WHEN running archive_sample_sheet in the run directory
    run_dir_flow_cell: RunDirFlowCell = RunDirFlowCell(
        flow_cell_dir=dragen_flow_cell_dir,
        status_db=base_store,
        housekeeper_api=real_housekeeper_api,
    )
    run_dir_flow_cell.archive_sample_sheet()

    # THEN assert the archiving is skipped
    assert "Sample sheet already included!" in caplog.text


def test_filter_sample_sheets(
    caplog,
    real_housekeeper_api: HousekeeperAPI,
    dragen_flow_cell_dir: Path,
    timestamp: datetime.datetime,
    base_store: Store,
    helpers: StoreHelpers,
):
    archived_sample_sheet: Tag = Tag(id=1, name="archived_sample_sheet")
    samplesheet: Tag = Tag(id=2, name="samplesheet")
    # GIVEN a list of files
    file1: File = File(id=1, path="path/to/file1", tags=[])
    file2: File = File(id=2, path="path/to/file2", tags=[archived_sample_sheet])
    file3: File = File(id=3, path="path/to/file3", tags=[samplesheet])
    file4: File = File(id=4, path="path/to/file4", tags=[archived_sample_sheet, samplesheet])
    version: Version = Version(id=1, bundle_id=1, files=[file1, file2, file3, file4])

    bundle_data: Dict = {"name": "HLG5GDRXY", "created": timestamp, "files": [], version: version}
    helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=bundle_data)

    # WHEN filtering out files tagged with neither archived_sample_sheet nor samplesheet
    run_dir_flow_cell: RunDirFlowCell = RunDirFlowCell(
        flow_cell_dir=dragen_flow_cell_dir,
        status_db=base_store,
        housekeeper_api=real_housekeeper_api,
    )
    filtered_files: List[File] = run_dir_flow_cell.filter_on_sample_sheets(
        [file1, file2, file3, file4]
    )

    # THEN the list should contain file2, file3 and file4 but not file1
    assert file1 not in filtered_files
    assert file2 in filtered_files
    assert file3 in filtered_files
    assert file4 in filtered_files

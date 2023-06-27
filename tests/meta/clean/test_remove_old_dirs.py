import datetime
from pathlib import Path
from typing import Dict

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.clean import clean_run_directories
from cg.store import Store
from tests.store_helpers import StoreHelpers


def test_remove_an_old_flow_cell_dir_skip_failing_flow_cell(
    caplog,
    real_housekeeper_api: HousekeeperAPI,
    dragen_flow_cell_dir: Path,
    timestamp: datetime.datetime,
    base_store: Store,
    helpers: StoreHelpers,
):
    # GIVEN an old flow cell which is not tagged as archived but which is present in Housekeeper

    bundle_data: Dict = {"name": "HLG5GDRXY", "created": timestamp, "files": []}

    helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=bundle_data)

    real_housekeeper_api.add_and_include_file_to_latest_version(
        bundle_name="HLG5GDRXY",
        file=Path(dragen_flow_cell_dir, "SampleSheet.csv"),
        tags=["samplesheet"],
    )

    # WHEN running the clean remove_old_flow_cell_dirs
    clean_run_directories(
        days_old=21,
        dry_run=False,
        housekeeper_api=real_housekeeper_api,
        run_directory=dragen_flow_cell_dir,
        status_db=base_store,
    )
    # THEN assert that the error is excepted
    assert "UNIQUE constraint failed: file.path" in caplog.text

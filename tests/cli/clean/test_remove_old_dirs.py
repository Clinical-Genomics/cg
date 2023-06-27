import datetime
from pathlib import Path
from typing import Dict

from cg.apps.cgstats.db.models import Version
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.clean import clean, clean_run_directories
from cg.models.cg_config import CGConfig, CleanConfig, CleanDirs, FlowCellRunDirs, Sequencers
from cg.store import Store
from click.testing import CliRunner
from tests.store_helpers import StoreHelpers


def test_remove_old_flow_cell_dirs_skip_failing_flow_cell(
    cli_runner: CliRunner,
    caplog,
    cg_context: CGConfig,
    dragen_flow_cell_dir: Path,
    dragen_flow_cell_full_name: str,
    timestamp: datetime.datetime,
):
    # GIVEN an old flow cell which is not tagged as archived but which is present in Housekeeper
    version: Version = cg_context.housekeeper_api.new_version(created_at=timestamp)
    cg_context.housekeeper_api.include(version_obj=version)
    sequencer: Sequencers = Sequencers()
    flow_cell_run_dirs: FlowCellRunDirs = FlowCellRunDirs(sequencer=sequencer)

    clean_dirs: CleanDirs = CleanDirs(sample_sheets_dir_name=str(dragen_flow_cell_dir))
    clean_config: CleanConfig = CleanConfig(
        flow_cells=clean_dirs, flow_cell_run_dirs=flow_cell_run_dirs
    )

    cg_context.clean = clean_config

    cg_context.housekeeper_api.add_and_include_file_to_latest_version(
        bundle_name="HLG5GDRXY",
        file=Path(dragen_flow_cell_dir, "SampleSheet.csv"),
        tags=["archived_sample_sheet"],
    )

    # WHEN running the clean remove_old_flow_cell_dirs
    cli_runner.invoke(clean, ["remove-old-flow-cell-run-dirs"], obj=cg_context)

    # THEN assert that the error is caught

    # THEN assert that the removal of other flow cell directories continued
    return True


def test_remove_an_old_flow_cell_dir_skip_failing_flow_cell(
    cli_runner: CliRunner,
    caplog,
    real_housekeeper_api: HousekeeperAPI,
    dragen_flow_cell_dir: Path,
    dragen_flow_cell_full_name: str,
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

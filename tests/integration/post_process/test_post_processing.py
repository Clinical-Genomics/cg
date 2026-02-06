import shutil
from datetime import date
from pathlib import Path
from typing import cast

import pytest
from click.testing import CliRunner, Result
from housekeeper.store.store import Store as HousekeeperStore

from cg.cli.base import base
from cg.store.models import PacbioSequencingRun, PacbioSMRTCell, PacbioSMRTCellMetrics
from cg.store.store import Store
from tests.integration.utils import IntegrationTestPaths
from tests.store_helpers import StoreHelpers


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_post_processing(
    status_db: Store,
    helpers: StoreHelpers,
    housekeeper_db: HousekeeperStore,
    test_run_paths: IntegrationTestPaths,
):
    cli_runner = CliRunner()

    # GIVEN a config file with valid database URIs and directories
    config_path: Path = test_run_paths.cg_config_file
    test_root_dir: Path = test_run_paths.test_root_dir

    # GIVEN a sample that has been sequenced using Pacbio and the resulting files exist on disk
    sample_id = "ACC15752A3"
    run_id = "r84202_20240522_133539"
    smrt_cell_id = "EA094869"

    helpers.add_sample(store=status_db, internal_id=sample_id)

    src = Path("tests", "fixtures", "devices", "pacbio", "SMRTcells", run_id).resolve()
    dst = Path(test_root_dir, "pacbio_data_dir", run_id).resolve()

    print(f"DEBUG: Copying from {src} (exists: {src.exists()})")
    print(f"DEBUG: Copying to {dst}")

    shutil.copytree(src, dst, dirs_exist_ok=True)

    # WHEN running post-process all
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            config_path.as_posix(),
            "-l",
            "DEBUG",
            "post-process",
            "all",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0

    # THEN a PacbioSequencingRun was persisted with the parsed data
    created_sequencing_run: PacbioSequencingRun = status_db.get_pacbio_sequencing_run_by_run_id(
        run_id
    )

    assert created_sequencing_run.run_id == run_id
    assert created_sequencing_run.instrument_name == "Wilma"

    # THEN PacbioSMRTCellMetrics was persisted with the parsed data
    smrt_cell_metrics: list[PacbioSMRTCellMetrics] = created_sequencing_run.smrt_cell_metrics

    assert len(smrt_cell_metrics) == 1
    metrics: PacbioSMRTCellMetrics = smrt_cell_metrics[0]

    assert metrics.barcoded_hifi_mean_read_length == 14477
    assert metrics.device.samples[0].internal_id == sample_id

    # THEN a PacbioSMRTCell was persisted with the parsed data
    smrt_cell = cast(PacbioSMRTCell, metrics.device)
    assert smrt_cell.internal_id == smrt_cell_id

    # THEN the BAM file was stored in the Sample housekeeper bundle with the correct path
    today = today = date.today()

    sample_files = housekeeper_db.get_files(bundle_name=sample_id).all()
    assert (
        f"{sample_id}/{today}/m84202_240522_155607_s2.hifi_reads.bc2004.bam" == sample_files[0].path
    )

    # THEN the correct files was stored in the SMRTCell housekeeper bundle
    smrtcell_files = [
        file.path for file in housekeeper_db.get_files(bundle_name=smrt_cell.internal_id).all()
    ]
    assert [
        f"{smrt_cell_id}/{today}/barcodes.report.json",
        f"{smrt_cell_id}/{today}/control.report.json",
        f"{smrt_cell_id}/{today}/loading.report.json",
        f"{smrt_cell_id}/{today}/raw_data.report.json",
        f"{smrt_cell_id}/{today}/smrtlink-datasets.json",
        f"{smrt_cell_id}/{today}/m84202_240522_155607_s2.ccs_report.json",
    ] == smrtcell_files

    # THEN a file was created to mark the run as validated
    assert Path(test_root_dir, "pacbio_data_dir", run_id, "1_B01", "is_valid").is_file()

    # THEN a file was created to mark post processing as completed
    assert Path(
        test_root_dir, "pacbio_data_dir", run_id, "1_B01", "post_processing_completed"
    ).is_file()

import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from housekeeper.store.store import Store as HousekeeperStore

from cg.cli.base import base
from cg.store.models import PacbioSequencingRun, PacbioSMRTCellMetrics
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

    sample_id = "ACC15752A3"

    helpers.add_sample(store=status_db, internal_id=sample_id)
    run_id = "r84202_20240522_133539"

    shutil.copytree(
        Path("tests/fixtures/devices/pacbio/SMRTcells/", run_id),
        Path(test_root_dir, "pacbio_data_dir", run_id),
        # ignore=lambda src, names: [".DS_Store"],
    )

    # WHEN running nallo start-available
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            config_path.as_posix(),
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

    # THEN a PacbioSMRTCellMetrics was persisted with the parsed data
    smrt_cell_metrics: list[PacbioSMRTCellMetrics] = created_sequencing_run.smrt_cell_metrics

    assert len(smrt_cell_metrics) == 1
    assert smrt_cell_metrics[0].barcoded_hifi_mean_read_length == 14477
    assert smrt_cell_metrics[0].device.samples[0].internal_id == sample_id

    # THEN the BAM file was stored in the Sample housekeeper bundle
    files = housekeeper_db.get_files(bundle_name=sample_id).all()
    assert "m84202_240522_155607_s2.hifi_reads.bc2004.bam" in files[0].path

    # TODO:
    # assert smrtcell bundles
    # assert post processing complete file was created

"""Test CLI function to get sequencing runs from StatusDB."""

from datetime import datetime

from click.testing import CliRunner

from cg.cli.get import get
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.store.models import IlluminaFlowCell, IlluminaSequencingRun
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_get_sequencing_run_wrong_device_id(cli_runner: CliRunner, base_context: CGConfig):
    """Test that trying to get a sequencing run using a non-existing device id fails."""
    # GIVEN a database

    # WHEN getting a non-existent sequencing run
    result = cli_runner.invoke(get, ["sequencing-run", "does_not_exist"], obj=base_context)

    # THEN the command exits with a non-zero exit code
    assert result.exit_code == EXIT_FAIL


def test_get_sequencing_run_required(
    cli_runner: CliRunner,
    new_demultiplex_context: CGConfig,
    novaseq_x_flow_cell_id: str,
):
    """Test to get a sequencing run using only the required arguments."""
    # GIVEN a database with a sequencing run

    # WHEN getting the sequencing run
    result = cli_runner.invoke(
        get, ["sequencing-run", novaseq_x_flow_cell_id], obj=new_demultiplex_context
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS


def test_get_sequencing_run_output(
    cli_runner: CliRunner,
    new_demultiplex_context: CGConfig,
    novaseq_x_flow_cell_id: str,
):
    """Test that the output of the get sequencing-run command has the correct data."""
    # GIVEN a database with a sequencing run
    status_db: Store = new_demultiplex_context.status_db
    sequencing_run: IlluminaSequencingRun = (
        status_db.get_illumina_sequencing_run_by_device_internal_id(novaseq_x_flow_cell_id)
    )

    # WHEN getting the sequencing run
    result = cli_runner.invoke(
        get, ["sequencing-run", novaseq_x_flow_cell_id], obj=new_demultiplex_context
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the sequencing run data is printed to the console
    assert sequencing_run.device.internal_id in result.output
    assert sequencing_run.sequencer_type in result.output
    assert sequencing_run.sequencer_name in result.output
    assert str(sequencing_run.sequencing_started_at.date()) in result.output
    assert str(sequencing_run.sequencing_completed_at.date()) in result.output
    assert sequencing_run.data_availability in result.output


def test_get_sequencing_run_archived_at_none(
    cli_runner: CliRunner,
    new_demultiplex_context: CGConfig,
    novaseq_x_flow_cell_id: str,
):
    """Test the output when there is no archived_at date."""
    # GIVEN a non-archived Illumina sequencing run
    status_db: Store = new_demultiplex_context.status_db
    sequencing_run: IlluminaSequencingRun = (
        status_db.get_illumina_sequencing_run_by_device_internal_id(novaseq_x_flow_cell_id)
    )
    sequencing_run.archived_at = None

    # WHEN getting a sequencing run
    result = cli_runner.invoke(
        get, ["sequencing-run", novaseq_x_flow_cell_id], obj=new_demultiplex_context
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN log that the sequencing run is not archived
    assert "No" in result.output


def test_get_sequencing_run_archived_at_date(
    cli_runner: CliRunner,
    new_demultiplex_context: CGConfig,
    novaseq_x_flow_cell_id: str,
    timestamp: datetime,
):
    """Test that the output has the run's archived at date."""
    # GIVEN a database with an archived sequencing run
    status_db: Store = new_demultiplex_context.status_db
    sequencing_run: IlluminaSequencingRun = (
        status_db.get_illumina_sequencing_run_by_device_internal_id(novaseq_x_flow_cell_id)
    )
    sequencing_run.archived_at = timestamp

    # WHEN getting the sequencing run
    result = cli_runner.invoke(
        get, ["sequencing-run", novaseq_x_flow_cell_id], obj=new_demultiplex_context
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the archived time should be in the output
    assert str(timestamp.date()) in result.output


def test_get_sequencing_run_samples_without_samples(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers, caplog
):
    """Test the output when there are no samples associated with the run."""
    # GIVEN a database with a sequencing run without related samples
    status_db: Store = base_context.status_db
    flow_cell: IlluminaFlowCell = helpers.ensure_illumina_flow_cell(store=status_db)
    helpers.ensure_illumina_sequencing_run(store=status_db, flow_cell=flow_cell)

    # WHEN getting a sequencing run with the --samples flag
    result = cli_runner.invoke(
        get,
        ["sequencing-run", flow_cell.internal_id, "--samples"],
        obj=base_context,
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN a message about no samples should have been displayed
    assert "No samples found on sequencing run" in caplog.text


def test_get_sequencing_run_samples(
    cli_runner: CliRunner, new_demultiplex_context: CGConfig, novaseq_x_flow_cell_id: str
):
    """Test that the output has the samples of the sequencing run."""
    # GIVEN a database with a sequencing run with related samples
    status_db: Store = new_demultiplex_context.status_db
    sequencing_run: IlluminaSequencingRun = (
        status_db.get_illumina_sequencing_run_by_device_internal_id(novaseq_x_flow_cell_id)
    )

    # WHEN getting a sequencing run with the --samples flag
    result = cli_runner.invoke(
        get,
        ["sequencing-run", novaseq_x_flow_cell_id, "--samples"],
        obj=new_demultiplex_context,
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN all related samples should be listed in the output
    for metric in sequencing_run.sample_metrics:
        assert metric.sample.internal_id in result.output


def test_get_sequencing_run_no_samples(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers
):
    """Test that a getting a sequencing run without samples prints no samples."""
    # GIVEN a database with a flow cell without related samples
    status_db: Store = base_context.status_db
    flow_cell: IlluminaFlowCell = helpers.ensure_illumina_flow_cell(store=status_db)
    helpers.ensure_illumina_sequencing_run(store=status_db, flow_cell=flow_cell)

    # WHEN getting a sequencing run with the --no-samples flag
    result = cli_runner.invoke(
        get, ["sequencing-run", flow_cell.internal_id, "--no-samples"], obj=base_context
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS


def test_get_flow_cell_no_samples_with_samples(
    cli_runner: CliRunner, new_demultiplex_context: CGConfig, novaseq_x_flow_cell_id: str
):
    """Test that the output has the data of the flow cell."""
    # GIVEN a database with a sequencing run with related samples
    status_db: Store = new_demultiplex_context.status_db
    sequencing_run: IlluminaSequencingRun = (
        status_db.get_illumina_sequencing_run_by_device_internal_id(novaseq_x_flow_cell_id)
    )

    # WHEN getting a sequencing run with the --no-samples flag
    result = cli_runner.invoke(
        get, ["sequencing-run", novaseq_x_flow_cell_id, "--no-samples"], obj=new_demultiplex_context
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN no related samples should be listed in the output
    for metric in sequencing_run.sample_metrics:
        assert metric.sample.internal_id not in result.output

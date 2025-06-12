"""This script tests the cli method to set data availability of sequencing runs in StatusDB."""

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.set.base import set_sequencing_run
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, SequencingRunDataAvailability
from cg.models.cg_config import CGConfig
from cg.store.models import IlluminaSequencingRun
from cg.store.store import Store


def test_set_sequencing_run_non_existent_id(
    cli_runner: CliRunner, base_context: CGConfig, caplog: LogCaptureFixture
):
    """Test to set a sequencing run that does not exist."""
    # GIVEN an empty database

    # WHEN trying to set a sequencing run that does not exist
    flow_cell_id: str = "non-existent-id"
    result = cli_runner.invoke(set_sequencing_run, [flow_cell_id], obj=base_context)

    # THEN it should exit successfully but print in console that sequencing run was not found
    assert result.exit_code == EXIT_FAIL
    assert f"Sequencing run with {flow_cell_id} not found" in caplog.text


def test_set_sequencing_run_required(
    cli_runner: CliRunner,
    new_demultiplex_context: CGConfig,
    novaseq_x_flow_cell_id: str,
    caplog: LogCaptureFixture,
):
    """Test to set a sequencing run using only the required arguments."""
    # GIVEN a database with a sequencing run

    # WHEN setting a sequencing run
    result = cli_runner.invoke(
        set_sequencing_run, [novaseq_x_flow_cell_id], obj=new_demultiplex_context
    )

    # THEN it should have been set
    assert result.exit_code == EXIT_FAIL
    assert "Please provide a data availability status" in caplog.text


def test_set_sequencing_run_data_availability(
    cli_runner: CliRunner,
    new_demultiplex_context: CGConfig,
    novaseq_x_flow_cell_id: str,
):
    """Test that the updated sequencing run get the data availability we send in."""
    # GIVEN a database with a sequencing run with a data availability different from 'requested'"
    status_db: Store = new_demultiplex_context.status_db
    data_availability = SequencingRunDataAvailability.statuses()[2]
    run_before_update: IlluminaSequencingRun = (
        status_db.get_illumina_sequencing_run_by_device_internal_id(novaseq_x_flow_cell_id)
    )
    assert run_before_update.data_availability != data_availability

    # WHEN setting the data availability of the sequencing run to 'requested'
    result = cli_runner.invoke(
        set_sequencing_run,
        ["--data-availability", data_availability, novaseq_x_flow_cell_id],
        obj=new_demultiplex_context,
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the data availability of the sequencing run is updated correctly
    updated_run: IlluminaSequencingRun = (
        status_db.get_illumina_sequencing_run_by_device_internal_id(novaseq_x_flow_cell_id)
    )
    assert updated_run.data_availability == data_availability

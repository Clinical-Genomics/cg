"""Test CLI functions to get flow cells in the Status database."""
from datetime import datetime

from cg.cli.get import get
from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner

from cg.store.models import Flowcell, Sample
from tests.store_helpers import StoreHelpers


def test_get_flow_cell_bad_flow_cell(cli_runner: CliRunner, base_context: CGConfig):
    """Test to get a flow cell using a non-existing flow cell"""
    # GIVEN an empty database

    # WHEN getting a flow cell
    result = cli_runner.invoke(get, ["flow-cell", "dummy_name"], obj=base_context)

    # THEN it should complain in missing flow cell instead of getting a flow cell
    assert result.exit_code == EXIT_FAIL


def test_get_flow_cell_required(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test to get a flow cell using only the required arguments."""
    # GIVEN a database with a flow cell
    flow_cell: Flowcell = helpers.add_flowcell(disk_store)
    assert disk_store.Flowcell.query.count() == 1

    # WHEN getting a flow cell

    result = cli_runner.invoke(get, ["flow-cell", flow_cell.name], obj=base_context)

    # THEN it should have been returned
    assert result.exit_code == EXIT_SUCCESS


def test_get_flow_cell_output(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the data of the flow cell."""
    # GIVEN a database with a flow cell with data
    flow_cell: Flowcell = helpers.add_flowcell(disk_store)
    flow_cell_name = flow_cell.name
    sequencer_type = disk_store.Flowcell.query.first().sequencer_type
    sequencer_name = disk_store.Flowcell.query.first().sequencer_name
    sequenced_at_date = str(disk_store.Flowcell.query.first().sequenced_at.date())
    status = disk_store.Flowcell.query.first().status

    # WHEN getting a flow cell
    result = cli_runner.invoke(get, ["flow-cell", flow_cell.name], obj=base_context)

    # THEN it should have been returned
    assert result.exit_code == EXIT_SUCCESS
    assert flow_cell_name in result.output
    assert sequencer_type in result.output
    assert sequencer_name in result.output
    assert sequenced_at_date in result.output
    assert status in result.output


def test_get_flow_cell_archived_at_none(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the data of the flow cell."""
    # GIVEN a database with a flowcell with data
    flow_cell: Flowcell = helpers.add_flowcell(disk_store, archived_at=None)

    # WHEN getting a flow  cell
    result = cli_runner.invoke(get, ["flow-cell", flow_cell.name], obj=base_context)

    # THEN it should have been returned
    assert result.exit_code == EXIT_SUCCESS
    assert "No" in result.output


def test_get_flowcell_archived_at_date(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the data of the flow cell."""
    # GIVEN a database with a flowcell with data
    archived_at: datetime = datetime.now()
    flow_cell: Flowcell = helpers.add_flowcell(disk_store, archived_at=archived_at)
    archived_at_date: str = str(archived_at.date())

    # WHEN getting a flow cell
    result = cli_runner.invoke(get, ["flow-cell", flow_cell.name], obj=base_context)

    # THEN it should have been returned
    assert result.exit_code == EXIT_SUCCESS
    assert archived_at_date in result.output


def test_get_flow_cell_samples_without_samples(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers, caplog
):
    """Test that the output without samples."""
    # GIVEN a database with a flow cell without related samples
    flow_cell: Flowcell = helpers.add_flowcell(disk_store)

    # WHEN getting a flow cell with the --samples flag
    result = cli_runner.invoke(get, ["flow-cell", flow_cell.name, "--samples"], obj=base_context)

    # THEN exist successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN a message about no samples should have been displayed
    assert "No samples found on flow cell" in caplog.text


def test_get_flow_cell_samples(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the samples of the flow cell."""
    # GIVEN a database with a flow cell with related samples
    samples: Sample = helpers.add_samples(store=disk_store)
    flow_cell: Flowcell = helpers.add_flowcell(store=disk_store, samples=samples)

    # WHEN getting a flow cell with the --samples flag
    result = cli_runner.invoke(get, ["flow-cell", flow_cell.name, "--samples"], obj=base_context)

    print(result.output)
    # THEN all related samples should be listed in the output
    assert result.exit_code == EXIT_SUCCESS
    for sample in disk_store.Flowcell.query.first().samples:
        assert sample.internal_id in result.output


def test_get_flow_cell_no_samples_without_samples(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output shows no samples of the flow cell."""
    # GIVEN a database with a flow cell without related samples
    flow_cell: Flowcell = helpers.add_flowcell(disk_store)

    # WHEN getting a flow cell with the --no-samples flag
    result = cli_runner.invoke(get, ["flow-cell", flow_cell.name, "--no-samples"], obj=base_context)

    # THEN there are no samples to display but everything is OK
    assert result.exit_code == EXIT_SUCCESS


def test_get_flow_cell_no_samples_with_samples(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the data of the flow cell."""
    # GIVEN a database with a flow cell with related samples
    samples: Sample = helpers.add_samples(store=disk_store)
    flow_cell: Flowcell = helpers.add_flowcell(store=disk_store, samples=samples)

    # WHEN getting a flow cell with the --no-samples flag
    result = cli_runner.invoke(get, ["flow-cell", flow_cell.name, "--no-samples"], obj=base_context)

    # THEN no related samples should be listed in the output
    assert result.exit_code == EXIT_SUCCESS
    for sample in disk_store.Flowcell.query.first().samples:
        assert sample.internal_id not in result.output

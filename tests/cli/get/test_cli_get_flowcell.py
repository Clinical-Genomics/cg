"""This script tests the cli methods to get flowcells in status-db"""
from datetime import datetime

from cg.cli.get import get
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner
from tests.store_helpers import StoreHelpers


def test_get_flowcell_bad_flowcell(cli_runner: CliRunner, base_context: CGConfig):
    """Test to get a flow cell using a non-existing flow cell"""
    # GIVEN an empty database

    # WHEN getting a flow cell
    name = "dummy_name"
    result = cli_runner.invoke(get, ["flowcell", name], obj=base_context)

    # THEN it should complain in missing flow cell instead of getting a flow cell
    assert result.exit_code == 1


def test_get_flowcell_required(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test to get a flow cell using only the required arguments."""
    # GIVEN a database with a flow cell
    flow_cell = helpers.add_flowcell(disk_store)
    flow_cell_name = flow_cell.name
    assert disk_store.Flowcell.query.count() == 1

    # WHEN getting a flow cell

    result = cli_runner.invoke(get, ["flowcell", flow_cell_name], obj=base_context)

    # THEN it should have been get
    assert result.exit_code == 0


def test_get_flowcell_output(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the data of the flow cell."""
    # GIVEN a database with a flow cell with data
    flow_cell = helpers.add_flowcell(disk_store)
    flow_cell_name = flow_cell.name
    sequencer_type = disk_store.Flowcell.query.first().sequencer_type
    sequencer_name = disk_store.Flowcell.query.first().sequencer_name
    sequenced_at_date = str(disk_store.Flowcell.query.first().sequenced_at.date())
    status = disk_store.Flowcell.query.first().status

    # WHEN getting a flowcell
    result = cli_runner.invoke(get, ["flowcell", flow_cell_name], obj=base_context)

    # THEN it should have been get
    assert result.exit_code == 0
    assert flow_cell_name in result.output
    assert sequencer_type in result.output
    assert sequencer_name in result.output
    assert sequenced_at_date in result.output
    assert status in result.output


def test_get_flowcell_archived_at_none(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the data of the flow cell."""
    # GIVEN a database with a flowcell with data
    flowcell = helpers.add_flowcell(disk_store, archived_at=None)
    archived_at = "No"

    # WHEN getting a flowcell
    result = cli_runner.invoke(get, ["flowcell", flowcell.name], obj=base_context)

    # THEN it should have been get
    assert result.exit_code == 0
    assert archived_at in result.output


def test_get_flowcell_archived_at_date(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the data of the flow cell."""
    # GIVEN a database with a flowcell with data
    archived_at = datetime.now()
    flowcell = helpers.add_flowcell(disk_store, archived_at=archived_at)
    archived_at_date = str(archived_at.date())

    # WHEN getting a flowcell
    result = cli_runner.invoke(get, ["flowcell", flowcell.name], obj=base_context)

    # THEN it should have been get
    assert result.exit_code == 0
    assert archived_at_date in result.output


def test_get_flowcell_samples_without_samples(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers, caplog
):
    """Test that the output has the data of the flow cell."""
    # GIVEN a database with a flowcell without related samples
    flowcell = helpers.add_flowcell(disk_store)
    assert not disk_store.Flowcell.query.first().samples

    # WHEN getting a flowcell with the --samples flag
    result = cli_runner.invoke(get, ["flowcell", flowcell.name, "--samples"], obj=base_context)

    # THEN a message about no samples should have been displayed
    assert result.exit_code == 0
    assert "no samples found on flowcell" in caplog.text


def test_get_flowcell_samples(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the data of the flow cell."""
    # GIVEN a database with a flowcell with related samples
    samples = helpers.add_samples(disk_store)
    flowcell = helpers.add_flowcell(disk_store, samples=samples)
    assert disk_store.Flowcell.query.first().samples

    # WHEN getting a flowcell with the --samples flag
    result = cli_runner.invoke(get, ["flowcell", flowcell.name, "--samples"], obj=base_context)

    # THEN all related samples should be listed in the output
    assert result.exit_code == 0
    for sample in disk_store.Flowcell.query.first().samples:
        assert sample.internal_id in result.output


def test_get_flowcell_no_samples_without_samples(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the data of the flow cell."""
    # GIVEN a database with a flowcell without related samples
    flowcell = helpers.add_flowcell(disk_store)
    assert not disk_store.Flowcell.query.first().samples

    # WHEN getting a flowcell with the --no-samples flag
    result = cli_runner.invoke(get, ["flowcell", flowcell.name, "--no-samples"], obj=base_context)

    # THEN there are no samples to display but everything is OK
    assert result.exit_code == 0


def test_get_flowcell_no_samples_with_samples(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the data of the flow cell."""
    # GIVEN a database with a flowcell with related samples
    samples = helpers.add_samples(disk_store)
    flowcell = helpers.add_flowcell(disk_store, samples=samples)
    assert disk_store.Flowcell.query.first().samples

    # WHEN getting a flowcell with the --no-samples flag
    db_uri = disk_store.uri

    result = cli_runner.invoke(get, ["flowcell", flowcell.name, "--no-samples"], obj=base_context)

    # THEN no related samples should be listed in the output
    assert result.exit_code == 0
    for sample in disk_store.Flowcell.query.first().samples:
        assert sample.internal_id not in result.output

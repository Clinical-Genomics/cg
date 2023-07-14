"""This script tests the cli methods to set flow cells in status-db."""
from cg.cli.set.base import flowcell
from cg.constants import FLOWCELL_STATUS
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner

from cg.store.models import Flowcell

SUCCESS = 0


def test_set_flowcell_bad_flowcell(cli_runner: CliRunner, base_context: CGConfig):
    """Test to set a flow cell using a non-existing flowcell."""
    # GIVEN an empty database

    # WHEN setting a flow cell
    flow_cell_name = "dummy_name"
    result = cli_runner.invoke(flowcell, [flow_cell_name], obj=base_context)

    # THEN it should complain in missing flow cell instead of setting a flow cell
    assert result.exit_code != SUCCESS


def test_set_flowcell_required(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers
):
    """Test to set a flow cell using only the required arguments."""
    # GIVEN a database with a flow cell
    flow_cell_name = helpers.add_flowcell(base_store).name
    assert base_store._get_query(table=Flowcell).count() == 1

    # WHEN setting a flowcell
    result = cli_runner.invoke(flowcell, [flow_cell_name], obj=base_context)

    # THEN it should have been set
    assert result.exit_code == SUCCESS


def test_set_flowcell_status(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers
):
    """Test that the updated flow_cell get the status we send in."""
    # GIVEN a database with a flow cell
    flow_cell_name = helpers.add_flowcell(base_store).name
    status = FLOWCELL_STATUS[2]
    flow_cell_query = base_store._get_query(table=Flowcell)
    assert flow_cell_query.first().status != status

    # WHEN setting a flowcell
    result = cli_runner.invoke(flowcell, ["--status", status, flow_cell_name], obj=base_context)

    # THEN it should have been set
    assert result.exit_code == SUCCESS
    assert flow_cell_query.count() == 1
    assert flow_cell_query.first().status == status

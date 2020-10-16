"""This script tests the cli methods to set flowcells in status-db"""

from cg.cli.set.base import flowcell
from cg.constants import FLOWCELL_STATUS
from cg.store import Store

SUCCESS = 0


def test_set_flowcell_bad_flowcell(cli_runner, base_context):
    """Test to set a flowcell using a non-existing flowcell """
    # GIVEN an empty database

    # WHEN setting a flowcell
    flowcell_name = "dummy_name"
    result = cli_runner.invoke(flowcell, [flowcell_name], obj=base_context)

    # THEN then it should complain in missing flowcell instead of setting a flowcell
    assert result.exit_code != SUCCESS


def test_set_flowcell_required(cli_runner, base_context, base_store: Store, helpers):
    """Test to set a flowcell using only the required arguments"""
    # GIVEN a database with a flowcell
    flowcell_name = helpers.add_flowcell(base_store).name
    assert base_store.Flowcell.query.count() == 1

    # WHEN setting a flowcell
    result = cli_runner.invoke(flowcell, [flowcell_name], obj=base_context)

    # THEN then it should have been set
    assert result.exit_code == SUCCESS


def test_set_flowcell_status(cli_runner, base_context, base_store: Store, helpers):
    """Test that the updated flowcell get the status we send in"""
    # GIVEN a database with a flowcell
    flowcell_name = helpers.add_flowcell(base_store).name
    status = FLOWCELL_STATUS[2]
    assert base_store.Flowcell.query.first().status != status

    # WHEN setting a flowcell
    result = cli_runner.invoke(flowcell, ["--status", status, flowcell_name], obj=base_context)

    # THEN then it should have been set
    assert result.exit_code == SUCCESS
    assert base_store.Flowcell.query.count() == 1
    assert base_store.Flowcell.query.first().status == status

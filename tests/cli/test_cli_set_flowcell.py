"""This script tests the cli methods to set flowcells in status-db"""
from datetime import datetime

from cg.constants import FLOWCELL_STATUS
from cg.store import Store


def test_set_flowcell_bad_flowcell(invoke_cli, disk_store: Store):
    """Test to set a flowcell using a non-existing flowcell """
    # GIVEN an empty database

    # WHEN setting a flowcell
    db_uri = disk_store.uri
    flowcell_name = 'dummy_name'
    result = invoke_cli(['--database', db_uri, 'set', 'flowcell', flowcell_name])

    # THEN then it should complain in missing flowcell instead of setting a flowcell
    assert result.exit_code == 1


def test_set_flowcell_required(invoke_cli, disk_store: Store):
    """Test to set a flowcell using only the required arguments"""
    # GIVEN a database with a flowcell
    flowcell_name = add_flowcell(disk_store).name
    assert disk_store.Flowcell.query.count() == 1

    # WHEN setting a flowcell
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'set', 'flowcell', flowcell_name])

    # THEN then it should have been set
    assert result.exit_code == 0


def test_set_flowcell_status(invoke_cli, disk_store: Store):
    """Test that the updated flowcell get the status we send in"""
    # GIVEN a database with a flowcell
    flowcell_name = add_flowcell(disk_store).name
    status = FLOWCELL_STATUS[2]
    assert disk_store.Flowcell.query.first().status != status

    # WHEN setting a flowcell
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'set', 'flowcell',
         '--status', status, flowcell_name])

    # THEN then it should have been set
    assert result.exit_code == 0
    assert disk_store.Flowcell.query.count() == 1
    assert disk_store.Flowcell.query.first().status == status


def add_flowcell(disk_store, flowcell_id='flowcell_test'):
    """utility function to set a flowcell to use in tests"""
    flowcell = disk_store.add_flowcell(name=flowcell_id, sequencer='dummy_sequencer',
                                       sequencer_type='hiseqx',
                                       date=datetime.now())
    disk_store.add_commit(flowcell)
    return flowcell

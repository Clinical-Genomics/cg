
from cg.store import Store
from cg.cli import report


def test_cli_report(invoke_cli, disk_store: Store):
    # GIVEN an empty database

    # WHEN calling the report command
    db_uri = disk_store.uri
    result = invoke_cli(['--database', db_uri, 'report'])

    # THEN success
    assert result.exit_code == 0


def test_cli_report_delivery_no_parameters(invoke_cli, disk_store: Store):
    # GIVEN an empty database

    # WHEN calling the report delivery command without parameters
    db_uri = disk_store.uri
    result = invoke_cli(['--database', db_uri, 'report', 'delivery'])

    # THEN fail
    assert result.exit_code != 0


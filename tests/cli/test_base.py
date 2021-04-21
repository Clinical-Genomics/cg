import logging
from pathlib import Path

import cg
from cg.cli.base import base, init
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner, Result


def test_cli_version(cli_runner: CliRunner):
    # GIVEN I want to see the version of the program
    # WHEN asking to see the version
    result: Result = cli_runner.invoke(base, ["--version"])
    # THEN it should display the version of the program
    # THEN it should print the name and version of the tool only
    assert cg.__title__ in result.output
    assert cg.__version__ in result.output


def test_list_commands(cli_runner: CliRunner):
    # WHEN using simplest command 'cg'
    result = cli_runner.invoke(base, [])
    # THEN it should just work ;-)
    assert result.exit_code == 0


def test_missing_command(cli_runner: CliRunner):
    # WHEN invoking a missing command
    result = cli_runner.invoke(cg, ["i_dont_exist"])
    # THEN context should abort
    assert result.exit_code != 0


def test_cli_init(cli_runner: CliRunner, base_context: CGConfig, caplog):
    caplog.set_level(logging.INFO)
    # GIVEN you want to setup a new database using the CLI
    database = "./test_db.sqlite3"
    database_path = Path(database)
    database_uri = f"sqlite:///{database}"
    base_context.status_db_ = Store(uri=database_uri)
    with cli_runner.isolated_filesystem():
        assert database_path.exists() is False

        # WHEN calling "init"
        result = cli_runner.invoke(init, [], obj=base_context)

        # THEN it should setup the database with some tables
        assert result.exit_code == 0
        assert database_path.exists()
        assert len(Store(database_uri).engine.table_names()) > 0

        # GIVEN the database already exists
        # WHEN calling the init function
        result = cli_runner.invoke(init, [], obj=base_context)

        # THEN it should print an error and give error exit code
        assert result.exit_code != 0
        assert "Database already exists" in caplog.text

        # GIVEN the database already exists
        # WHEN calling "init" with "--reset"
        result = cli_runner.invoke(init, ["--reset"], input="Yes", obj=base_context)

        # THEN it should re-setup the tables and print new tables
        assert result.exit_code == 0
        assert "Success!" in caplog.text

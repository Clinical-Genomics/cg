from pathlib import Path

import cg
from cg.store import Store


def test_cli_version(invoke_cli):
    # GIVEN I want to see the version of the program
    # WHEN asking to see the version
    result = invoke_cli(["--version"])
    # THEN it should display the version of the program
    # THEN it should print the name and version of the tool only
    assert cg.__title__ in result.output
    assert cg.__version__ in result.output


def test_list_commands(invoke_cli):
    # WHEN using simplest command 'cg'
    result = invoke_cli()
    # THEN it should just work ;-)
    assert result.exit_code == 0


def test_missing_command(invoke_cli):
    # WHEN invoking a missing command
    result = invoke_cli(["idontexist"])
    # THEN context should abort
    assert result.exit_code != 0


def test_cli_init(cli_runner, invoke_cli):

    # GIVEN you want to setup a new database using the CLI
    database = "./test_db.sqlite3"
    database_path = Path(database)
    database_uri = f"sqlite:///{database}"
    with cli_runner.isolated_filesystem():
        assert database_path.exists() is False

        # WHEN calling "init"
        result = invoke_cli(["--database", database_uri, "init"])

        # THEN it should setup the database with some tables
        assert result.exit_code == 0
        assert database_path.exists()
        assert len(Store(database_uri).engine.table_names()) > 0

        # GIVEN the database already exists
        # WHEN calling the init function
        result = invoke_cli(["--database", database_uri, "init"])

        # THEN it should print an error and give error exit code
        assert result.exit_code != 0
        assert "Database already exists" in result.output

        # GIVEN the database already exists
        # WHEN calling "init" with "--reset"
        result = invoke_cli(["--database", database_uri, "init", "--reset"], input="Yes")

        # THEN it should re-setup the tables and print new tables
        assert result.exit_code == 0
        assert "Success!" in result.output

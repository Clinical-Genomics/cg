"""Tests for rsync API"""
import glob
import logging

from cg.cli.deliver.base import rsync
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cgmodels.cg.constants import Pipeline


def test_rsync_help(cli_runner):
    """Test to run the rsync function"""
    # GIVEN a cli runner

    # WHEN running cg deliver rsync
    result = cli_runner.invoke(rsync, ["--dry-run", "--help"])

    # THEN assert the command exists without problems
    assert result.exit_code == EXIT_SUCCESS
    # THEN assert the information is printed
    assert "The folder generated using the" in result.output


def test_run_rsync_command(cg_context: CGConfig, cli_runner, helpers, caplog, mocker):
    """Test generating the rsync command for covid ticket"""
    caplog.set_level(logging.INFO)

    # Given a valid Sars-cov-2 case
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id="angrybird",
        case_id=999999,
        data_analysis=Pipeline.SARS_COV_2,
    )
    sample = helpers.add_sample(store=cg_context.status_db, ticket=999999)
    helpers.add_relationship(store=cg_context.status_db, sample=sample, case=case)
    cg_context.status_db.add_commit()

    # GIVEN file exists
    mocker.patch.object(glob, "glob")
    glob.glob.return_value = [
        "/folder_structure/angrybird/yet_another_folder/filename_999999_data_999.csv"
    ]

    # WHEN running deliver rsync command
    result = cli_runner.invoke(rsync, ["--dry-run", "999999"], obj=cg_context)

    # THEN command executed successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN process generates command string for linking analysis files
    assert "cust000/inbox/999999/ server.name.se:/some/cust000/path/999999/" in caplog.text
    # THEN process generates command string for linking report file
    assert (
        "rsync -rvL /folder_structure/angrybird/yet_another_folder/filename_999999_data_999.csv "
        "server.name.se:/another/cust000/foldername/" in caplog.text
    )


def test_run_rsync_command_no_file(cg_context: CGConfig, cli_runner, helpers, caplog, mocker):
    """Test generating the rsync command for covid ticket"""
    caplog.set_level(logging.INFO)

    # Given a valid Sars-cov-2 case
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id="angrybird",
        case_id=999999,
        data_analysis=Pipeline.SARS_COV_2,
    )
    sample = helpers.add_sample(store=cg_context.status_db, ticket=999999)
    helpers.add_relationship(store=cg_context.status_db, sample=sample, case=case)
    cg_context.status_db.add_commit()

    # WHEN running deliver rsync command
    result = cli_runner.invoke(rsync, ["--dry-run", "999999"], obj=cg_context)

    # THEN command executed successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN process generates command string for linking analysis files
    assert "cust000/inbox/999999/ server.name.se:/some/cust000/path/999999/" in caplog.text
    # THEN process generates command string for linking report file
    caplog.set_level(logging.ERROR)
    assert "No report file could be found" in caplog.text


def test_run_rsync_command_no_case(cg_context: CGConfig, cli_runner, helpers, caplog):
    """Test generating the rsync command for ticket that doesnt exist"""
    caplog.set_level(logging.INFO)

    # Given an invalid ticket id where case was not created

    # WHEN running deliver rsync command
    result = cli_runner.invoke(rsync, ["--dry-run", "9898989898"], obj=cg_context)

    # THEN command failed successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN process generates error message that case cant be found
    assert "Could not find any cases for ticket_id" in caplog.text


def test_run_rsync_command_not_sarscov(cg_context: CGConfig, cli_runner, helpers, caplog):
    """Test generating the rsync command for non-covid ticket"""
    caplog.set_level(logging.INFO)

    # Given a valid Sars-cov-2 case
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id="angryfox",
        case_id=987654,
        data_analysis=Pipeline.BALSAMIC,
    )
    sample = helpers.add_sample(store=cg_context.status_db, ticket=987654)
    helpers.add_relationship(store=cg_context.status_db, sample=sample, case=case)
    cg_context.status_db.add_commit()

    # WHEN running deliver rsync command
    result = cli_runner.invoke(rsync, ["--dry-run", "987654"], obj=cg_context)

    # THEN command executed successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN process will not inform about linking report file
    assert "Delivering report for SARS-COV-2 analysis" not in caplog.text

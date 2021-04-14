import logging

from cg.cli.backup import backup, fetch_flowcell
from cg.meta.backup import BackupApi
from cg.models.cg_config import CGConfig
from click.testing import CliRunner


def test_run_backup_base_cmd(cli_runner: CliRunner, cg_context: CGConfig):
    # GIVEN a context with the backup specific configurations
    assert cg_context.backup.root
    # GIVEN that there is no backup meta api available
    assert "backup_api" not in cg_context.meta_apis

    # WHEN running the base command
    result = cli_runner.invoke(backup, ["fetch-flowcell", "--help"], obj=cg_context)

    # THEN assert that the command exits without any problems
    assert result.exit_code == 0
    # THEN assert that the BackupAPI was instantiated and added
    assert isinstance(cg_context.meta_apis["backup_api"], BackupApi)


def test_run_fetch_flowcell_dry_run_no_flowcell_specified(
    cli_runner: CliRunner, backup_context: CGConfig, caplog
):
    caplog.set_level(logging.INFO)
    # GIVEN a context with a backup_api
    assert "backup_api" in backup_context.meta_apis
    # GIVEN that there are no flowcells set to "requested" in status_db
    assert not backup_context.status_db.flowcells(status="requested").first()

    # WHEN running the fetch flowcell command without specifying any flowcell in dry run mode
    result = cli_runner.invoke(fetch_flowcell, ["--dry-run"], obj=backup_context)

    # THEN assert that it exits without any problems
    assert result.exit_code == 0
    # THEN assert that it is communicated that no flowcells are requested
    assert "no flowcells requested" in caplog.text


def test_run_fetch_flowcell_dry_run_retrieval_time(
    cli_runner: CliRunner, backup_context: CGConfig, caplog, mocker
):
    caplog.set_level(logging.INFO)
    # GIVEN a context with a backup_api
    assert "backup_api" in backup_context.meta_apis
    # GIVEN that there are no flowcells set to "requested" in status_db
    assert not backup_context.status_db.flowcells(status="requested").first()
    # GIVEN that the backup api returns a retrieval time
    expected_time = 60
    mocker.patch("cg.meta.backup.BackupApi.fetch_flowcell", return_value=expected_time)

    # WHEN running the fetch flowcell command without specifying any flowcell in dry run mode
    result = cli_runner.invoke(fetch_flowcell, ["--dry-run"], obj=backup_context)

    # THEN assert that it exits without any problems
    assert result.exit_code == 0
    # THEN assert that it is communicated that a retrieval time was found
    assert "Retrieval time" in caplog.text


def test_run_fetch_flowcell_non_existing_flowcell(
    cli_runner: CliRunner, backup_context: CGConfig, caplog
):
    # GIVEN a context with a backup api
    # GIVEN a non existing flowcell id
    flowcell_id = "hello"
    assert backup_context.status_db.flowcell(flowcell_id) is None

    # WHEN running the command with the non existing flowcell id
    result = cli_runner.invoke(fetch_flowcell, ["--flowcell", flowcell_id], obj=backup_context)

    # THEN assert that it exits with a non zero exit code
    assert result.exit_code != 0
    # THEN assert that it was communicated that the flowcell does not exist
    assert f"{flowcell_id}: not found" in caplog.text

import logging

from cg.models.cg_config import CGConfig
from cg.cli.workflow.send_fastq.base import start, start_available, run, send_fastq


def test_start_available(caplog, case_id, cli_runner, send_fastq_context: CGConfig):
    caplog.set_level(logging.INFO)
    # GIVEN a case with no analysis
    send_fastq_context.status_db.family(internal_id=case_id).analyses = []
    send_fastq_context.status_db.commit()

    # WHEN the start_available command is invoked
    cli_runner.invoke(start_available, ["--dry-run"], obj=send_fastq_context)

    # THEN the right case should be found and the run command should be reached
    assert "Running %s in dry-run mode", case_id in caplog.text


def test_send_fastq(caplog, cli_runner, send_fastq_context):
    # GIVEN no arguments passed

    # WHEN the command is invoked
    result = cli_runner.invoke(send_fastq, obj=send_fastq_context)
    print(result.output)
    # THEN the command should exit successfully
    assert result.exit_code == 0
    # THEN the help text should be echoed
    assert "help" in result.output


def test_start(caplog, case_id, cli_runner, send_fastq_context: CGConfig):
    caplog.set_level(logging.INFO)

    # WHEN the start command is invoked
    cli_runner.invoke(start, [case_id, "--dry-run"], obj=send_fastq_context)

    # THEN the run command should be reached
    assert "Running %s in dry-run mode", case_id in caplog.text


def test_run(caplog, case_id, cli_runner, send_fastq_context):
    caplog.set_level(logging.INFO)

    # WHEN the start_available command is invoked
    cli_runner.invoke(run, [case_id, "--dry-run"], obj=send_fastq_context)

    # THEN the run command should be reached
    assert "Running %s in dry-run mode", case_id in caplog.text

import logging
import datetime as dt
from cg.cli.workflow.send_fastq.base import start, start_available, run, send_fastq
from cg.store import models


def test_start_available(caplog, case_id: str, cli_runner, sample_id: str, send_fastq_context):
    """Tests the start_available command for the send_fastq workflow"""
    caplog.set_level(logging.INFO)
    # GIVEN a case with no analysis, a sample that has been sequenced and a send_fastq context
    case_obj: models.Family = send_fastq_context.status_db.family(internal_id=case_id)
    case_obj.analyses = []
    sample_obj: models.Sample = send_fastq_context.status_db.sample(internal_id=sample_id)
    sample_obj.sequenced_at = dt.datetime.now()

    # WHEN the start_available command is invoked
    cli_runner.invoke(start_available, ["--dry-run"], obj=send_fastq_context)

    # THEN the right case should be found and the run command should be reached
    assert f"Running {case_id} in dry-run mode" in caplog.text


def test_send_fastq(caplog, cli_runner, send_fastq_context):
    """Tests the send_fastq command without arguments"""
    # GIVEN no arguments passed

    # WHEN the command is invoked
    result = cli_runner.invoke(send_fastq, obj=send_fastq_context)
    print(result.output)
    # THEN the command should exit successfully
    assert result.exit_code == 0
    # THEN the help text should be echoed
    assert "help" in result.output


def test_start(caplog, case_id: str, cli_runner, send_fastq_context):
    """Tests the start command for the send_fastq workflow"""
    # GIVEN a send_fastq context
    caplog.set_level(logging.INFO)

    # WHEN the start command is invoked
    cli_runner.invoke(start, [case_id, "--dry-run"], obj=send_fastq_context)

    # THEN the run command should be reached
    assert f"Running {case_id} in dry-run mode" in caplog.text


def test_run(caplog, case_id: str, cli_runner, send_fastq_context):
    """Tests the run command for the send_fastq workflow"""
    # GIVEN a send_fastq context
    caplog.set_level(logging.INFO)

    # WHEN the start_available command is invoked
    cli_runner.invoke(run, [case_id, "--dry-run"], obj=send_fastq_context)

    # THEN the run command should be reached
    assert f"Running {case_id} in dry-run mode" in caplog.text

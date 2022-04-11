import logging

from cgmodels.cg.constants import Pipeline

from cg.cli.upload.clinical_delivery import upload_fastq, auto_fastq
from cg.store import models


def test_auto_fastq_not_started(
    analysis_obj: models.Analysis, caplog, fastq_context, cli_runner, case_id: str
):
    """Tests if the command finds a non-uploaded analysis and attempts to start it"""
    caplog.set_level(logging.INFO)
    # GIVEN a case to be delivered
    analysis_obj.pipeline = Pipeline.FASTQ
    fastq_context.status_db.commit()
    fastq_context.status_db.session.close()
    # WHEN the upload command is invoked with dry run
    cli_runner.invoke(auto_fastq, ["--dry-run"], obj=fastq_context)

    # THEN the content of the .sh file should be in the caplog
    assert f"#SBATCH --job-name={case_id}_rsync" in caplog.text


def test_upload_fastq(caplog, fastq_context, cli_runner, case_id: str):
    """Test if the function successfully creates an sbatch script"""
    caplog.set_level(logging.INFO)
    # GIVEN a case to be delivered

    # WHEN the upload command is invoked with dry run
    cli_runner.invoke(upload_fastq, [case_id, "--dry-run"], obj=fastq_context)

    # THEN the content of the .sh file should be in the caplog
    assert f"#SBATCH --job-name={case_id}_rsync" in caplog.text

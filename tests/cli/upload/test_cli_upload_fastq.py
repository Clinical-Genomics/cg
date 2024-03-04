import logging

from cg.cli.upload.clinical_delivery import auto_fastq
from cg.constants import DataDelivery
from cg.constants.constants import Workflow
from cg.store.models import Analysis


def test_auto_fastq_not_started(
    analysis_obj: Analysis, caplog, base_context, cli_runner, case_id: str
):
    """Tests if the command finds a non-uploaded analysis and attempts to start it"""
    caplog.set_level(logging.INFO)
    # GIVEN a case to be delivered
    analysis_obj.workflow = Workflow.FASTQ
    analysis_obj.case.data_delivery = DataDelivery.FASTQ
    base_context.status_db.session.commit()
    base_context.status_db.session.close()
    # WHEN the upload command is invoked with dry run
    cli_runner.invoke(auto_fastq, ["--dry-run"], obj=base_context)

    # THEN the content of the .sh file should be in the caplog
    assert f"#SBATCH --job-name={case_id}_rsync" in caplog.text

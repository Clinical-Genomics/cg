from pathlib import Path

from cg.constants.priority import SlurmQos
from cg.meta.workflow.send_fastq import SendFastqAnalysisAPI
from cg.store import models
from tests.cli.workflow.send_fastq.conftest import fixture_send_fastq_context, fixture_fastq_case
from tests.cli.workflow.conftest import tb_api


def test_upload_bundle_statusdb(
    case_id: str, customer_id, mocker, send_fastq_context, ticket_nr, tmpdir_factory
):
    # GIVEN that a case has no analyses and a delivery folder is presemt
    send_fastq_api: SendFastqAnalysisAPI = send_fastq_context.meta_apis["analysis_api"]
    status_db = send_fastq_context.status_db
    for analysis in status_db.family(internal_id=case_id).analyses:
        status_db.delete_commit(analysis)
    ticket_dir: str = tmpdir_factory.mktemp(str(ticket_nr))
    mocker.patch.object(SendFastqAnalysisAPI, "get_deliverables_file_path")
    SendFastqAnalysisAPI.get_deliverables_file_path.return_value = ticket_dir
    assert status_db.family(internal_id=case_id).analyses == []

    # WHEN the upload_bundle_statusdb is called
    send_fastq_api.upload_bundle_statusdb(case_id=case_id)
    case_obj = status_db.family(internal_id=case_id)
    # THEN the analysis should be in statusdb and have both the upload_started at and the uploaded_at fields filled.
    assert case_obj.analyses[0]
    assert case_obj.analyses[0].upload_started_at and case_obj.analyses[0].uploaded_at


def test_convert_case_priority(case_id, send_fastq_context):
    # GIVEN a case with prio other than 4
    case_obj = send_fastq_context.status_db.family(internal_id=case_id)

    # WHEN convert_case_priority is called
    slurm_qos = send_fastq_context.meta_apis["analysis_api"].convert_case_priority(
        case_obj=case_obj
    )
    # THEN SlurmQos.LOW should ne returned
    assert slurm_qos == SlurmQos.LOW

    # GIVEN a case with prio 4
    case_obj.priority_int = 4

    # WHEN convert_case_priority is called
    slurm_qos = send_fastq_context.meta_apis["analysis_api"].convert_case_priority(
        case_obj=case_obj
    )
    # THEN SlurmQos.HIGH should ne returned
    assert slurm_qos == SlurmQos.HIGH

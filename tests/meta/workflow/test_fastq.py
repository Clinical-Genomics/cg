from cg.meta.workflow.fastq import FastqAnalysisAPI
from cg.store import models, Store
from tests.cli.workflow.conftest import tb_api
from tests.cli.workflow.fastq.conftest import fixture_fastq_context, fixture_fastq_case


def test_upload_bundle_statusdb(
    case_id: str, customer_id, mocker, fastq_context, ticket_nr: int, tmpdir_factory
):
    """Tests the status_db upload for the FastqAnalysisAPI"""
    # GIVEN that a fastq_context
    fastq_api: FastqAnalysisAPI = fastq_context.meta_apis["analysis_api"]
    status_db: Store = fastq_context.status_db

    # GIVEN a case with no analyses
    for analysis in status_db.family(internal_id=case_id).analyses:
        status_db.delete_commit(analysis)
    ticket_dir: str = tmpdir_factory.mktemp(str(ticket_nr))

    # GIVEN that a delivery folder is present
    mocker.patch.object(FastqAnalysisAPI, "get_deliverables_file_path")
    FastqAnalysisAPI.get_deliverables_file_path.return_value = ticket_dir
    assert status_db.family(internal_id=case_id).analyses == []

    # WHEN the upload_bundle_statusdb is called
    fastq_api.upload_bundle_statusdb(case_id=case_id)
    case_obj: models.Family = status_db.family(internal_id=case_id)

    # THEN the analysis should be in statusdb and have both the upload_started at and the uploaded_at fields filled.
    assert case_obj.analyses[0]
    assert case_obj.analyses[0].upload_started_at and case_obj.analyses[0].uploaded_at

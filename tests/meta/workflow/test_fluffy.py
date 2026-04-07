from mock import Mock, create_autospec
from pytest_mock import MockerFixture

from cg.constants.priority import SlurmQos
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case, CaseSample, Sample
from cg.store.store import Store


def test_run_fluffy(cg_context: CGConfig, mocker: MockerFixture):
    # GIVEN a FluffyAnalysisAPI
    analysis_api = FluffyAnalysisAPI(cg_context)

    status_db = create_autospec(Store)
    status_db.get_case_by_internal_id = Mock(
        return_value=create_autospec(
            Case,
            links=[create_autospec(CaseSample, sample=create_autospec(Sample, order="order"))],
            slurm_priority=SlurmQos.NORMAL,
        )
    )
    analysis_api.status_db = status_db

    # GIVEN that the subprocess runs successfully
    run_pipeline_call = mocker.patch.object(analysis_api.process, "run_command")

    # WHEN calling run_fluffy without batch_ref
    analysis_api.run_fluffy(
        case_id="case_id",
        dry_run=False,
        workflow_config="workflow_config",
        batch_ref=False,
        use_bwa_mem=True,
    )

    # THEN the subprocess should have been called with the correct flags
    run_pipeline_call.assert_called_once_with(
        [
            "--config",
            "workflow_config",
            "--sample",
            f"{analysis_api.root_dir}/case_id/SampleSheet_order.csv",
            "--project",
            f"{analysis_api.root_dir}/case_id/fastq",
            "--out",
            f"{analysis_api.root_dir}/case_id/output",
            "--analyse",
            "",
            "--bwa-mem",
            "--slurm_params",
            f"qos:{SlurmQos.NORMAL}",
        ],
        dry_run=False,
    )


def test_run_fluffy_with_batch_ref(cg_context: CGConfig, mocker: MockerFixture):
    # GIVEN a FluffyAnalysisAPI
    analysis_api = FluffyAnalysisAPI(cg_context)

    status_db = create_autospec(Store)
    status_db.get_case_by_internal_id = Mock(
        return_value=create_autospec(
            Case,
            links=[create_autospec(CaseSample, sample=create_autospec(Sample, order="order"))],
            slurm_priority=SlurmQos.NORMAL,
        )
    )
    analysis_api.status_db = status_db

    # GIVEN that the subprocess runs successfully
    run_pipeline_call = mocker.patch.object(analysis_api.process, "run_command")

    # WHEN calling run_fluffy with batch_ref True
    analysis_api.run_fluffy(
        case_id="case_id",
        dry_run=False,
        workflow_config="workflow_config",
        batch_ref=True,
        use_bwa_mem=True,
    )

    # THEN the subprocess should have been called with the correct flags
    run_pipeline_call.assert_called_once_with(
        [
            "--config",
            "workflow_config",
            "--sample",
            f"{analysis_api.root_dir}/case_id/SampleSheet_order.csv",
            "--project",
            f"{analysis_api.root_dir}/case_id/fastq",
            "--out",
            f"{analysis_api.root_dir}/case_id/output",
            "--analyse",
            "--batch-ref",
            "--bwa-mem",
            "--slurm_params",
            f"qos:{SlurmQos.NORMAL}",
        ],
        dry_run=False,
    )

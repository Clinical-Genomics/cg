import pytest
from mock import Mock, create_autospec
from pytest_mock import MockerFixture

from cg.constants.priority import SlurmQos
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import (
    CGConfig,
    FluffyConfig,
    FluffyUploadConfig,
    IlluminaConfig,
    RunInstruments,
)
from cg.store.models import Case, CaseSample, Sample
from cg.store.store import Store


@pytest.fixture
def fluffy_cg_config() -> CGConfig:
    return create_autospec(
        CGConfig,
        fluffy=FluffyConfig(
            root_dir="/fake/fluffy_root",
            binary_path="binary_path",
            config_path="config_path",
            sftp=FluffyUploadConfig(
                user="user",
                password="password",
                host="host",
                remote_path="remote_path",
                port=22,
            ),
        ),
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
    )


def test_run_fluffy(fluffy_cg_config: CGConfig, mocker: MockerFixture):
    # GIVEN a FluffyAnalysisAPI
    analysis_api = FluffyAnalysisAPI(fluffy_cg_config)

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
            "--slurm_params",
            f"qos:{SlurmQos.NORMAL}",
        ],
        dry_run=False,
    )


def test_run_fluffy_with_batch_ref(fluffy_cg_config: CGConfig, mocker: MockerFixture):
    # GIVEN a FluffyAnalysisAPI
    analysis_api = FluffyAnalysisAPI(fluffy_cg_config)

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
            "--slurm_params",
            f"qos:{SlurmQos.NORMAL}",
        ],
        dry_run=False,
    )

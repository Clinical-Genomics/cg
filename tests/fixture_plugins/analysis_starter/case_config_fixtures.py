from pathlib import Path

import pytest

from cg.constants import Workflow
from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig


@pytest.fixture
def get_nextflow_case_config_dict(
    nextflow_case_id: str,
    nextflow_case_path: Path,
    nextflow_config_profiles: list[str],
    nextflow_repository: str,
    nextflow_pipeline_revision: str,
) -> callable:
    """
    Return a case config dictionary factory for Nextflow pipelines. The returned factory can be
    called by adding the workflow as parameter to obtain the case config dictionary.
    Example usage:
        config: dict = get_nextflow_case_config_dict(workflow="raredisease")
    """

    def _make_dict(workflow) -> dict:
        return {
            "case_id": nextflow_case_id,
            "config_profiles": nextflow_config_profiles,
            "workflow": workflow,
            "case_priority": SlurmQos.NORMAL,
            "nextflow_config_file": Path(
                nextflow_case_path, f"{nextflow_case_id}_nextflow_config.json"
            ).as_posix(),
            "params_file": Path(
                nextflow_case_path, f"{nextflow_case_id}_params_file.yaml"
            ).as_posix(),
            "pipeline_repository": nextflow_repository,
            "pre_run_script": "",
            "revision": nextflow_pipeline_revision,
            "work_dir": Path(nextflow_case_path, "work").as_posix(),
        }

    return _make_dict


@pytest.fixture
def raredisease_case_config(
    nextflow_case_id: str,
    nextflow_case_path: Path,
    nextflow_config_profiles: list[str],
    nextflow_repository: str,
    nextflow_pipeline_revision: str,
) -> NextflowCaseConfig:

    return NextflowCaseConfig(
        case_id=nextflow_case_id,
        config_profiles=nextflow_config_profiles,
        workflow=Workflow.RAREDISEASE,
        case_priority=SlurmQos.NORMAL,
        nextflow_config_file=Path(
            nextflow_case_path, f"{nextflow_case_id}_nextflow_config.json"
        ).as_posix(),
        params_file=Path(nextflow_case_path, f"{nextflow_case_id}_params_file.yaml").as_posix(),
        pipeline_repository=nextflow_repository,
        pre_run_script="",
        revision=nextflow_pipeline_revision,
        work_dir=Path(nextflow_case_path, "work").as_posix(),
    )


@pytest.fixture
def rnafusion_case_config(nextflow_root: str, nextflow_case_id: str) -> NextflowCaseConfig:
    return NextflowCaseConfig(
        case_id=nextflow_case_id,
        workflow=Workflow.RNAFUSION,
        case_priority=SlurmQos.NORMAL,
        config_profiles=["myprofile"],
        nextflow_config_file=Path(
            nextflow_root, nextflow_case_id, f"{nextflow_case_id}_nextflow_config.json"
        ).as_posix(),
        params_file=Path(
            nextflow_root, nextflow_case_id, f"{nextflow_case_id}_params_file.yaml"
        ).as_posix(),
        pipeline_repository="https://some_url",
        pre_run_script="",
        revision="2.2.0",
        work_dir=Path(nextflow_root, nextflow_case_id, "work").as_posix(),
    )


@pytest.fixture
def taxprofiler_case_config(get_nextflow_case_config_dict: callable) -> NextflowCaseConfig:
    return NextflowCaseConfig(**get_nextflow_case_config_dict(workflow=Workflow.TAXPROFILER))

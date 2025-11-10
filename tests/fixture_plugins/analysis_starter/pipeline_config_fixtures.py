from collections.abc import Callable
from pathlib import Path

import pytest

from cg.models.cg_config import NalloConfig, RarediseaseConfig, RnafusionConfig, TaxprofilerConfig


@pytest.fixture
def get_nextflow_config_dict(
    nextflow_binary: Path,
    nextflow_root: str,
    conda_binary: Path,
    nf_analysis_platform_config_path: Path,
    nf_analysis_pipeline_config_path: Path,
    nf_analysis_pipeline_params_path: Path,
    nf_analysis_pipeline_resource_optimisation_path: Path,
    nextflow_repository: str,
    nextflow_pipeline_revision: str,
    email_address: str,
) -> callable:
    """
    Return a config dictionary factory for Nextflow pipelines. The returned factory can be called
    by adding the workflow as parameter to obtain the config dictionary.
    Example usage:
        config: dict = get_nextflow_config_dict(workflow="raredisease")
    """

    def _make_dict(workflow: str) -> dict:
        return {
            "binary_path": nextflow_binary.as_posix(),
            "compute_env": "nf_tower_compute_env",
            "conda_binary": conda_binary.as_posix(),
            "conda_env": f"S_{workflow}",
            "platform": str(nf_analysis_platform_config_path),
            "params": str(nf_analysis_pipeline_params_path),
            "config": str(nf_analysis_pipeline_config_path),
            "resources": str(nf_analysis_pipeline_resource_optimisation_path),
            "launch_directory": Path("path", "to", "launchdir").as_posix(),
            "workflow_bin_path": Path("workflow", "path").as_posix(),
            "profile": "myprofile",
            "references": Path("path", "to", "references").as_posix(),
            "repository": nextflow_repository,
            "revision": nextflow_pipeline_revision,
            "root": nextflow_root,
            "slurm": {
                "account": "development",
                "mail_user": email_address,
            },
            "tower_workflow": workflow,
        }

    return _make_dict


@pytest.fixture
def nallo_config_object(get_nextflow_config_dict: Callable) -> NalloConfig:
    config: dict = get_nextflow_config_dict(workflow="nallo")
    return NalloConfig(**config)


@pytest.fixture
def raredisease_config_object(get_nextflow_config_dict: Callable) -> RarediseaseConfig:
    config: dict = get_nextflow_config_dict(workflow="raredisease")
    return RarediseaseConfig(**config)


@pytest.fixture
def rnafusion_config_object(get_nextflow_config_dict: Callable) -> RnafusionConfig:
    config: dict = get_nextflow_config_dict(workflow="rnafusion")
    return RnafusionConfig(**config)


@pytest.fixture
def taxprofiler_config_object(get_nextflow_config_dict: Callable) -> TaxprofilerConfig:
    config: dict = get_nextflow_config_dict(workflow="taxprofiler")
    return TaxprofilerConfig(**config)

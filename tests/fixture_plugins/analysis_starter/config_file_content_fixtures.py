from pathlib import Path

import pytest

from cg.constants.priority import SlurmQos


@pytest.fixture
def nextflow_config_base_content(
    nf_analysis_pipeline_config_path: Path,
    nf_analysis_platform_config_path: Path,
    nf_analysis_pipeline_resource_optimisation_path: Path,
) -> str:
    content: str = (
        "\n"
        + nf_analysis_platform_config_path.read_text()
        + "\n"
        + nf_analysis_pipeline_config_path.read_text()
        + "\n"
        + nf_analysis_pipeline_resource_optimisation_path.read_text()
    )
    return content


@pytest.fixture
def nextflow_cluster_options() -> str:
    return f'process.clusterOptions = "-A development --qos={SlurmQos.NORMAL}"\n'


@pytest.fixture
def expected_nextflow_config_content(
    nextflow_cluster_options: str,
    nextflow_config_base_content: str,
) -> str:
    return nextflow_cluster_options + nextflow_config_base_content + "\n"

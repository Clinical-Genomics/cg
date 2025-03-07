from pathlib import Path

import pytest

from cg.constants.priority import SlurmQos
from cg.constants.symbols import NEW_LINE


@pytest.fixture
def nextflow_config_base_content(
    nf_analysis_pipeline_config_path: Path,
    nf_analysis_platform_config_path: Path,
    nf_analysis_pipeline_resource_optimisation_path: Path,
) -> str:
    content: str = (
        NEW_LINE
        + nf_analysis_platform_config_path.read_text()
        + NEW_LINE
        + nf_analysis_pipeline_config_path.read_text()
        + NEW_LINE
        + nf_analysis_pipeline_resource_optimisation_path.read_text()
    )
    return content


@pytest.fixture
def nextflow_cluster_options() -> str:
    return f'process.clusterOptions = "-A development --qos={SlurmQos.NORMAL}"{NEW_LINE}'


@pytest.fixture
def expected_raredisease_config_content(
    nextflow_cluster_options: str,
    nextflow_config_base_content: str,
) -> str:
    return nextflow_cluster_options + nextflow_config_base_content


@pytest.fixture
def expected_raredisease_params_file_content(
    raredisease_case_path: Path,
    raredisease_sample_sheet_path: Path,
    raredisease_gene_panel_path: Path,
    raredisease_managed_variants_path: Path,
) -> dict:
    return {
        "input": raredisease_sample_sheet_path,
        "outdir": raredisease_case_path,
        "target_bed_file": "twistexomecomprehensive_10.2_hg19_design.bed",
        "analysis_type": "wgs",
        "save_mapped_as_cram": True,
        "skip_germlinecnvcaller": True,
        "vcfanno_extra_resources": raredisease_managed_variants_path.as_posix(),
        "vep_filters_scout_fmt": raredisease_gene_panel_path.as_posix(),
        "someparam": "something",
    }

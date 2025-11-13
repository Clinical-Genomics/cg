from collections.abc import Callable
from pathlib import Path

import pytest

from cg.constants.observations import BalsamicObservationPanel
from cg.models.cg_config import (
    BalsamicConfig,
    LoqusDBDumpFiles,
    NalloConfig,
    RarediseaseConfig,
    RnafusionConfig,
    SlurmConfig,
    TaxprofilerConfig,
)


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
def cg_balsamic_config(tmp_path) -> BalsamicConfig:
    return BalsamicConfig(
        balsamic_cache=tmp_path / "balsamic_cache",
        bed_path=tmp_path / "beds",
        binary_path=tmp_path / "binary",
        cadd_path=tmp_path / "cadd",
        conda_binary=tmp_path / "conda",
        conda_env="balsamic_env",
        genome_interval_path=tmp_path / "intervals.interval_list",
        gens_coverage_female_path=tmp_path / "coverage_female.txt",
        gens_coverage_male_path=tmp_path / "coverage_male.txt",
        gnomad_af5_path=tmp_path / "gnomad_af5.vcf",
        head_job_partition="head-jobs",
        loqusdb_path=Path("mongodb://localhost:27017/loqusdb"),
        loqusdb_dump_files=LoqusDBDumpFiles(
            artefact_sv=tmp_path / "artefact_sv.vcf",
            artefact_snv=tmp_path / "artefact_snv.vcf",
            cancer_germline_snv=tmp_path / "cancer_germline_snv.vcf",
            cancer_somatic_snv=tmp_path / "cancer_somatic_snv.vcf",
            cancer_somatic_sv=tmp_path / "cancer_somatic_sv.vcf",
            clinical_snv=tmp_path / "clinical_snv.vcf",
            clinical_sv=tmp_path / "clinical_sv.vcf",
            cancer_somatic_snv_panels={
                BalsamicObservationPanel.MYELOID: tmp_path / "loqusdb_myeloid_dump",
                BalsamicObservationPanel.LYMPHOID: tmp_path / "loqusdb_lymphoid_dump",
                BalsamicObservationPanel.EXOME: tmp_path / "loqusdb_exome_dump",
            },
        ),
        panel_of_normals={
            "myeloid_short_name": Path("absolute_path_to_myeloid_pon_file.cnn"),
            "lymphoid_short_name": Path("absolute_path_to_lymphoid_pon_file.cnn"),
            "exome_short_name": Path("absolute_path_to_exome_pon_file.cnn"),
        },
        pon_path=tmp_path / "pon.cnn",
        root=tmp_path / "balsamic_root",
        sentieon_licence_path=tmp_path / "sentieon.lic",
        sentieon_licence_server="27001@sentieon-license",
        slurm=SlurmConfig(
            account="production",
            mail_user="balsamic@test.org",
        ),
        swegen_path="swegen",
        swegen_snv=tmp_path / "swegen_snv.vcf",
        swegen_sv=tmp_path / "swegen_sv.vcf",
    )


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

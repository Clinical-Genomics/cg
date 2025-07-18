from pathlib import Path

from pydantic import BaseModel

from cg.constants import Workflow
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class BalsamicConfigInput(BaseModel):
    conda_binary: str
    balsamic_binary: str
    analysis_dir: str
    analysis_workflow: str
    artefact_snv_observations: str
    balsamic_cache: str
    cadd_annotations: str
    cancer_germline_snv_observations: str
    cancer_germline_sv_observations: str
    cancer_somatic_sv_observations: str
    case_id: str
    clinical_snv_observations: str
    clinical_sv_observations: str
    fastq_path: str
    gender: str
    genome_interval: str
    genome_version: str
    gens_coverage_pon: str | None
    gnomad_min_af5: str | None
    normal_sample_name: str | None
    panel_bed: str | None = None
    pon_cnn: str | None = None
    exome: str | None = None
    sentieon_install_dir: str
    sentieon_license: str
    soft_filter_normal: str | None = None
    swegen_snv: str
    swegen_sv: str
    tumor_sample_name: str


class BalsamicCaseConfig(CaseConfig):
    account: str
    binary: str
    cluster_config: str
    conda_binary: str
    environment: str
    mail_user: str
    qos: str
    sample_config: Path
    workflow: Workflow = Workflow.BALSAMIC

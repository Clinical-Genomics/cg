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
    exome: bool = False
    sentieon_install_dir: str
    sentieon_license: str
    soft_filter_normal: bool = False
    swegen_snv: str
    swegen_sv: str
    tumor_sample_name: str

    def dump_to_cli(self) -> str:
        """Dump the Balsamic case config to a CLI command. None flags are excluded and boolean flags are converted to
        only add the flag."""
        base = f"{self.conda_binary} run {self.balsamic_binary} balsamic config case"
        args = {
            "--analysis-dir": self.analysis_dir,
            "--analysis-workflow": self.analysis_workflow,
            "--balsamic-cache": self.balsamic_cache,
            "--cadd-annotations": self.cadd_annotations,
            "--artefact-snv-observations": self.artefact_snv_observations,
            "--cancer-germline-snv-observations": self.cancer_germline_snv_observations,
            "--cancer-germline-sv-observations": self.cancer_germline_sv_observations,
            "--cancer-somatic-sv-observations": self.cancer_somatic_sv_observations,
            "--case-id": self.case_id,
            "--clinical-snv-observations": self.clinical_snv_observations,
            "--clinical-sv-observations": self.clinical_sv_observations,
            "--fastq-path": self.fastq_path,
            "--gender": self.gender,
            "--genome-interval": self.genome_interval,
            "--genome-version": self.genome_version,
            "--gens-coverage-pon": self.gens_coverage_pon,
            "--gnomad-min-af5": self.gnomad_min_af5,
            "--normal-sample-name": self.normal_sample_name,
            "--panel-bed": self.panel_bed,
            "--pon-cnn": self.pon_cnn,
            "--exome": self.exome,
            "--sentieon-install-dir": self.sentieon_install_dir,
            "--sentieon-license": self.sentieon_license,
            "--soft-filter-normal": self.soft_filter_normal,
            "--swegen-snv": self.swegen_snv,
            "--swegen-sv": self.swegen_sv,
            "--tumor-sample-name": self.tumor_sample_name,
        }
        for flag, value in args.items():
            if value is type(bool) and value:
                base += f" {flag}"
            elif value is not None:
                base += f" {flag} {value}"
        return base


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

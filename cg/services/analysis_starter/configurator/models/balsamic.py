from pathlib import Path

from pydantic import BaseModel

from cg.constants import SexOptions, Workflow
from cg.constants.constants import GenomeVersion
from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class BalsamicConfigInput(BaseModel):
    analysis_dir: Path
    analysis_workflow: Workflow
    artefact_snv_observations: Path
    balsamic_cache: Path
    conda_binary: Path
    conda_env: str
    balsamic_binary: Path
    cadd_annotations: Path
    cancer_germline_snv_observations: Path
    cancer_somatic_snv_observations: Path
    cancer_somatic_sv_observations: Path
    case_id: str
    clinical_snv_observations: Path
    clinical_sv_observations: Path
    fastq_path: Path
    gender: SexOptions
    genome_version: GenomeVersion
    gnomad_min_af5: Path | None = None
    normal_sample_name: str | None = None
    pon_cnn: Path | None = None
    sentieon_install_dir: Path
    sentieon_license: str
    soft_filter_normal: bool = False
    swegen_snv: Path
    swegen_sv: Path
    tumor_sample_name: str


class BalsamicConfigInputPanel(BalsamicConfigInput):
    exome: bool
    panel_bed: Path

    def dump_to_cli(self) -> str:
        """Dump the Balsamic case config to a CLI command. None flags are excluded and boolean flags are converted to
        only add the flag."""
        command = (
            f"{self.conda_binary} run --name {self.conda_env} {self.balsamic_binary} config case"
        )
        flags = {
            "--analysis-dir": self.analysis_dir,
            "--analysis-workflow": self.analysis_workflow,
            "--balsamic-cache": self.balsamic_cache,
            "--cadd-annotations": self.cadd_annotations,
            "--artefact-snv-observations": self.artefact_snv_observations,
            "--cancer-germline-snv-observations": self.cancer_germline_snv_observations,
            "--cancer-somatic-snv-observations": self.cancer_somatic_snv_observations,
            "--cancer-somatic-sv-observations": self.cancer_somatic_sv_observations,
            "--case-id": self.case_id,
            "--clinical-snv-observations": self.clinical_snv_observations,
            "--clinical-sv-observations": self.clinical_sv_observations,
            "--fastq-path": self.fastq_path,
            "--gender": self.gender,
            "--genome-version": self.genome_version,
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
        for flag, value in flags.items():
            if isinstance(value, bool):
                if value is True:
                    command += f" {flag}"
            elif value is not None:
                command += f" {flag} {value}"
        return command


class BalsamicConfigInputWGS(BalsamicConfigInput):
    artefact_sv_observations: Path
    genome_interval: Path
    gens_coverage_pon: Path

    def dump_to_cli(self) -> str:
        """Dump the Balsamic case config to a CLI command. None flags are excluded and boolean flags are converted to
        only add the flag."""
        command = (
            f"{self.conda_binary} run --name {self.conda_env} {self.balsamic_binary} config case"
        )
        flags = {
            "--analysis-dir": self.analysis_dir,
            "--analysis-workflow": self.analysis_workflow,
            "--balsamic-cache": self.balsamic_cache,
            "--cadd-annotations": self.cadd_annotations,
            "--artefact-snv-observations": self.artefact_snv_observations,
            "--artefact-sv-observations": self.artefact_sv_observations,
            "--cancer-germline-snv-observations": self.cancer_germline_snv_observations,
            "--cancer-somatic-snv-observations": self.cancer_somatic_snv_observations,
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
            "--pon-cnn": self.pon_cnn,
            "--sentieon-install-dir": self.sentieon_install_dir,
            "--sentieon-license": self.sentieon_license,
            "--soft-filter-normal": self.soft_filter_normal,
            "--swegen-snv": self.swegen_snv,
            "--swegen-sv": self.swegen_sv,
            "--tumor-sample-name": self.tumor_sample_name,
        }
        for flag, value in flags.items():
            if isinstance(value, bool):
                if value is True:
                    command += f" {flag}"
            elif value is not None:
                command += f" {flag} {value}"
        return command


class BalsamicCaseConfig(CaseConfig):
    account: str
    binary: Path
    cluster_config: Path
    conda_binary: Path
    environment: str
    mail_user: str
    qos: SlurmQos
    sample_config: Path
    workflow: Workflow = Workflow.BALSAMIC

    def get_start_command(self) -> str:
        return (
            "{conda_binary} run {binary} run analysis --account {account} --mail-user {mail_user} "
            "--qos {qos} --sample-config {sample_config} --cluster-config {cluster_config} --run-analysis "
            "--benchmark".format(**self.model_dump())
        )

from abc import abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from cg.constants import SexOptions, Workflow
from cg.constants.constants import GenomeVersion
from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class BalsamicConfigInput(BaseModel):
    analysis_dir: Path
    analysis_workflow: Workflow
    artefact_snv_observations: Path
    balsamic_binary: Path
    balsamic_cache: Path
    cache_version: str
    cadd_annotations: Path
    cancer_germline_snv_observations: Path
    cancer_somatic_snv_observations: Path
    cancer_somatic_sv_observations: Path
    case_id: str
    case_name: str
    clinical_snv_observations: Path
    clinical_sv_observations: Path
    conda_binary: Path
    conda_env: str
    fastq_path: Path
    gender: SexOptions
    genome_version: GenomeVersion
    gnomad_min_af5: Path
    normal_sample_name: str | None = None
    sentieon_install_dir: Path
    sentieon_license: str
    swegen_snv: Path
    swegen_sv: Path
    tumor_sample_name: str

    def dump_to_cli(self) -> str:
        """Dump the Balsamic case config to a CLI command. None flags are excluded and boolean flags are converted to
        only add the flag."""
        command = (
            f"{self.conda_binary} run --name {self.conda_env} {self.balsamic_binary} config case"
        )

        for flag, value in self._get_flags().items():
            if isinstance(value, bool):
                if value is True:
                    command += f" {flag}"
            elif value is not None:
                command += f" {flag} {value}"
        return command

    @abstractmethod
    def _get_flags(self) -> dict[str, Any]:
        pass


class BalsamicConfigInputPanel(BalsamicConfigInput):
    cancer_somatic_snv_panel_observations: Path | None = None
    exome: bool
    panel_bed: Path
    pon_cnn: Path | None = (
        None  # Equivalent to --gens-coverage-pon in wgs analysis, depends on the panel
    )
    soft_filter_normal: bool = False  # True for all panel analyses with a normal sample

    def _get_flags(self) -> dict[str, Any]:
        return {
            "--analysis-dir": self.analysis_dir,
            "--analysis-workflow": self.analysis_workflow,
            "--artefact-snv-observations": self.artefact_snv_observations,
            "--balsamic-cache": self.balsamic_cache,
            "--cache-version": self.cache_version,
            "--cadd-annotations": self.cadd_annotations,
            "--cancer-germline-snv-observations": self.cancer_germline_snv_observations,
            "--cancer-somatic-snv-observations": self.cancer_somatic_snv_observations,
            "--cancer-somatic-snv-panel-observations": self.cancer_somatic_snv_panel_observations,
            "--cancer-somatic-sv-observations": self.cancer_somatic_sv_observations,
            "--case-id": self.case_id,
            "--clinical-snv-observations": self.clinical_snv_observations,
            "--clinical-sv-observations": self.clinical_sv_observations,
            "--cust-case-id": self.case_name,
            "--fastq-path": self.fastq_path,
            "--gender": self.gender,
            "--genome-version": self.genome_version,
            "--gnomad-min-af5": self.gnomad_min_af5,
            "--normal-sample-name": self.normal_sample_name,
            "--panel-bed": self.panel_bed,
            "--exome": self.exome,  # MUST be after panel bed
            "--pon-cnn": self.pon_cnn,
            "--sentieon-install-dir": self.sentieon_install_dir,
            "--sentieon-license": self.sentieon_license,
            "--soft-filter-normal": self.soft_filter_normal,
            "--swegen-snv": self.swegen_snv,
            "--swegen-sv": self.swegen_sv,
            "--tumor-sample-name": self.tumor_sample_name,
        }


class BalsamicConfigInputWGS(BalsamicConfigInput):
    artefact_sv_observations: Path
    genome_interval: Path
    gens_coverage_pon: Path  # Equivalent to --pon-cnn in panel analysis, depends on the sex

    def _get_flags(self) -> dict[str, Any]:
        return {
            "--analysis-dir": self.analysis_dir,
            "--analysis-workflow": self.analysis_workflow,
            "--artefact-snv-observations": self.artefact_snv_observations,
            "--artefact-sv-observations": self.artefact_sv_observations,
            "--balsamic-cache": self.balsamic_cache,
            "--cache-version": self.cache_version,
            "--cadd-annotations": self.cadd_annotations,
            "--cancer-germline-snv-observations": self.cancer_germline_snv_observations,
            "--cancer-somatic-snv-observations": self.cancer_somatic_snv_observations,
            "--cancer-somatic-sv-observations": self.cancer_somatic_sv_observations,
            "--case-id": self.case_id,
            "--clinical-snv-observations": self.clinical_snv_observations,
            "--clinical-sv-observations": self.clinical_sv_observations,
            "--cust-case-id": self.case_name,
            "--fastq-path": self.fastq_path,
            "--gender": self.gender,
            "--genome-interval": self.genome_interval,
            "--genome-version": self.genome_version,
            "--gens-coverage-pon": self.gens_coverage_pon,
            "--gnomad-min-af5": self.gnomad_min_af5,
            "--normal-sample-name": self.normal_sample_name,
            "--sentieon-install-dir": self.sentieon_install_dir,
            "--sentieon-license": self.sentieon_license,
            "--swegen-snv": self.swegen_snv,
            "--swegen-sv": self.swegen_sv,
            "--tumor-sample-name": self.tumor_sample_name,
        }


class BalsamicCaseConfig(CaseConfig):
    account: str
    binary: Path
    conda_binary: Path
    environment: str
    head_job_partition: str
    qos: SlurmQos
    sample_config: Path
    workflow: Workflow = Workflow.BALSAMIC
    workflow_profile: Path | None = None

    def get_start_command(self) -> str:
        command = (
            "{conda_binary} run --name {environment} {binary} run analysis --account {account} "
            "--qos {qos} --sample-config {sample_config} --headjob-partition {head_job_partition} "
            "--run-analysis".format(**self.model_dump())
        )
        if self.workflow_profile:
            command += f" --workflow-profile {self.workflow_profile}"
        return command

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from cg.constants import Workflow
from cg.constants.constants import FileExtensions, FileFormat, MultiQC, WorkflowManager
from cg.constants.nextflow import NFX_WORK_DIR
from cg.constants.tb import AnalysisStatus
from cg.exc import CgError, MetricsQCError
from cg.io.controller import ReadFile, WriteFile
from cg.io.yaml import write_yaml_nextflow_style
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.nf_handlers import NextflowHandler, NfTowerHandler
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import (
    MetricsBase,
    MetricsDeliverablesCondition,
)
from cg.models.fastq import FastqFileMeta
from cg.models.nf_analysis import FileDeliverable, PipelineDeliverables
from cg.models.rnafusion.rnafusion import CommandArgs
from cg.utils import Process

LOG = logging.getLogger(__name__)


class NfAnalysisAPI(AnalysisAPI):
    """Parent class for handling NF-core analyses."""

    def __init__(self, config: CGConfig, workflow: Workflow):
        super().__init__(workflow=workflow, config=config)
        self.workflow: Workflow = workflow
        self.root_dir: str | None = None
        self.nfcore_workflow_path: str | None = None
        self.references: str | None = None
        self.profile: str | None = None
        self.conda_env: str | None = None
        self.conda_binary: str | None = None
        self.tower_binary_path: str | None = None
        self.tower_workflow: str | None = None
        self.account: str | None = None
        self.email: str | None = None
        self.compute_env_base: str | None = None
        self.revision: str | None = None
        self.nextflow_binary_path: str | None = None

    @property
    def root(self) -> str:
        return self.root_dir

    @property
    def process(self):
        if not self._process:
            self._process = Process(
                binary=self.tower_binary_path,
            )
        return self._process

    @process.setter
    def process(self, process: Process):
        self._process = process

    def get_profile(self, profile: str | None = None) -> str:
        """Get NF profiles."""
        return profile or self.profile

    def get_workflow_manager(self) -> str:
        """Get workflow manager from Tower."""
        return WorkflowManager.Tower.value

    def get_workflow_version(self, case_id: str) -> str:
        """Get pipeline version from config."""
        return self.revision

    def get_case_path(self, case_id: str) -> Path:
        """Path to case working directory."""
        return Path(self.root_dir, case_id)

    def get_sample_sheet_path(self, case_id: str) -> Path:
        """Path to sample sheet."""
        return Path(self.get_case_path(case_id), f"{case_id}_samplesheet").with_suffix(
            FileExtensions.CSV
        )

    def get_compute_env(self, case_id: str) -> str:
        """Get the compute environment for the head job based on the case priority."""
        return f"{self.compute_env_base}-{self.get_slurm_qos_for_case(case_id=case_id)}"

    @staticmethod
    def get_nextflow_config_path(nextflow_config: str | None = None) -> Path | None:
        """Path to Nextflow config file."""
        if nextflow_config:
            return Path(nextflow_config).absolute()

    def get_job_ids_path(self, case_id: str) -> Path:
        """Return the path to a Trailblazer config file containing Tower IDs."""
        return Path(self.root_dir, case_id, "tower_ids").with_suffix(FileExtensions.YAML)

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """Path to deliverables file for a case."""
        return Path(self.get_case_path(case_id), f"{case_id}_deliverables").with_suffix(
            FileExtensions.YAML
        )

    def get_metrics_deliverables_path(self, case_id: str) -> Path:
        """Return a path where the <case>_metrics_deliverables.yaml file should be located."""
        return Path(self.root_dir, case_id, f"{case_id}_metrics_deliverables").with_suffix(
            FileExtensions.YAML
        )

    def get_params_file_path(self, case_id: str, params_file: Path | None = None) -> Path:
        """Return parameters file or a path where the default parameters file for a case id should be located."""
        if params_file:
            return Path(params_file).absolute()
        return Path((self.get_case_path(case_id)), f"{case_id}_params_file").with_suffix(
            FileExtensions.YAML
        )

    def create_case_directory(self, case_id: str, dry_run: bool = False) -> None:
        """Create case directory."""
        if not dry_run:
            Path(self.get_case_path(case_id=case_id)).mkdir(parents=True, exist_ok=True)

    def get_log_path(self, case_id: str, workflow: str, log: str = None) -> Path:
        """Path to NF log."""
        if log:
            return log
        launch_time: str = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
        return Path(
            self.get_case_path(case_id),
            f"{case_id}_{workflow}_nextflow_{launch_time}",
        ).with_suffix(FileExtensions.LOG)

    def get_workdir_path(self, case_id: str, work_dir: Path | None = None) -> Path:
        """Path to NF work directory."""
        if work_dir:
            return work_dir.absolute()
        return Path(self.get_case_path(case_id), NFX_WORK_DIR)

    @staticmethod
    def extract_read_files(
        metadata: list[FastqFileMeta], forward_read: bool = False, reverse_read: bool = False
    ) -> list[str]:
        """Extract a list of fastq file paths for either forward or reverse reads."""
        if forward_read and not reverse_read:
            read_direction = 1
        elif reverse_read and not forward_read:
            read_direction = 2
        else:
            raise ValueError("Either forward or reverse needs to be specified")
        sorted_metadata: list = sorted(metadata, key=lambda k: k.path)
        return [
            fastq_file.path
            for fastq_file in sorted_metadata
            if fastq_file.read_direction == read_direction
        ]

    def verify_sample_sheet_exists(self, case_id: str, dry_run: bool = False) -> None:
        """Raise an error if sample sheet file is not found."""
        if not dry_run and not Path(self.get_sample_sheet_path(case_id=case_id)).exists():
            raise ValueError(f"No config file found for case {case_id}")

    def verify_deliverables_file_exists(self, case_id: str) -> None:
        """Raise an error if a deliverable file is not found."""
        if not Path(self.get_deliverables_file_path(case_id=case_id)).exists():
            raise CgError(f"No deliverables file found for case {case_id}")

    def write_params_file(self, case_id: str, workflow_parameters: dict) -> None:
        """Write params-file for analysis."""
        LOG.debug("Writing parameters file")
        write_yaml_nextflow_style(
            content=workflow_parameters,
            file_path=self.get_params_file_path(case_id=case_id),
        )

    @staticmethod
    def write_sample_sheet(
        content: list[list[Any]],
        file_path: Path,
        header: list[str],
    ) -> None:
        """Write sample sheet CSV file."""
        LOG.debug("Writing sample sheet")
        if header:
            content.insert(0, header)
        WriteFile.write_file_from_content(
            content=content,
            file_format=FileFormat.CSV,
            file_path=file_path,
        )

    @staticmethod
    def write_deliverables_file(
        deliverables_content: dict, file_path: Path, file_format=FileFormat.YAML
    ) -> None:
        """Write deliverables file."""
        WriteFile.write_file_from_content(
            content=deliverables_content, file_format=file_format, file_path=file_path
        )

    def write_trailblazer_config(self, case_id: str, tower_id: str) -> None:
        """Write Tower IDs to a file used as the Trailblazer config."""
        config_path: Path = self.get_job_ids_path(case_id=case_id)
        LOG.info(f"Writing Tower ID to {config_path.as_posix()}")
        WriteFile.write_file_from_content(
            content={case_id: [tower_id]},
            file_format=FileFormat.YAML,
            file_path=config_path,
        )

    def _run_analysis_with_nextflow(
        self, case_id: str, command_args: CommandArgs, dry_run: bool
    ) -> None:
        """Run analysis with given options using Nextflow."""
        self.process = Process(
            binary=self.nextflow_binary_path,
            environment=self.conda_env,
            conda_binary=self.conda_binary,
            launch_directory=self.get_case_path(case_id=case_id),
        )
        LOG.info("Workflow will be executed using Nextflow")
        parameters: list[str] = NextflowHandler.get_nextflow_run_parameters(
            case_id=case_id,
            pipeline_path=self.nfcore_workflow_path,
            root_dir=self.root_dir,
            command_args=command_args.dict(),
        )
        self.process.export_variables(
            export=NextflowHandler.get_variables_to_export(),
        )
        command: str = self.process.get_command(parameters=parameters)
        LOG.info(f"{command}")
        sbatch_number: int = NextflowHandler.execute_head_job(
            case_id=case_id,
            case_directory=self.get_case_path(case_id=case_id),
            slurm_account=self.account,
            email=self.email,
            qos=self.get_slurm_qos_for_case(case_id=case_id),
            commands=command,
            dry_run=dry_run,
        )
        LOG.info(f"Nextflow head job running as job: {sbatch_number}")

    def _run_analysis_with_tower(
        self, case_id: str, command_args: CommandArgs, dry_run: bool
    ) -> None:
        """Run analysis with given options using NF-Tower."""
        LOG.info("Workflow will be executed using Tower")
        if command_args.resume:
            from_tower_id: int = command_args.id or NfTowerHandler.get_last_tower_id(
                case_id=case_id,
                trailblazer_config=self.get_job_ids_path(case_id=case_id),
            )
            LOG.info(f"Workflow will be resumed from run with Tower id: {from_tower_id}.")
            parameters: list[str] = NfTowerHandler.get_tower_relaunch_parameters(
                from_tower_id=from_tower_id, command_args=command_args.dict()
            )
        else:
            parameters: list[str] = NfTowerHandler.get_tower_launch_parameters(
                tower_workflow=self.tower_workflow, command_args=command_args.dict()
            )
        self.process.run_command(parameters=parameters, dry_run=dry_run)
        if self.process.stderr:
            LOG.error(self.process.stderr)
        if not dry_run:
            tower_id = NfTowerHandler.get_tower_id(stdout_lines=self.process.stdout_lines())
            self.write_trailblazer_config(case_id=case_id, tower_id=tower_id)
        LOG.info(self.process.stdout)

    def run_analysis(
        self,
        case_id: str,
        command_args: CommandArgs,
        use_nextflow: bool,
        dry_run: bool = False,
    ) -> None:
        """Execute run analysis with given options."""
        if use_nextflow:
            self._run_analysis_with_nextflow(
                case_id=case_id,
                command_args=command_args,
                dry_run=dry_run,
            )
        else:
            self._run_analysis_with_tower(
                case_id=case_id,
                command_args=command_args,
                dry_run=dry_run,
            )

    @staticmethod
    def get_deliverables_template_content() -> list[dict]:
        """Return deliverables file template content."""
        raise NotImplementedError

    def get_deliverables_for_case(self, case_id: str) -> PipelineDeliverables:
        """Return PipelineDeliverables for a given case."""
        deliverable_template: list[dict] = self.get_deliverables_template_content()
        sample_id: str = self.status_db.get_samples_by_case_id(case_id).pop().internal_id
        files: list[FileDeliverable] = []
        for file in deliverable_template:
            for deliverable_field, deliverable_value in file.items():
                if deliverable_value is None:
                    continue
                file[deliverable_field] = file[deliverable_field].replace("CASEID", case_id)
                file[deliverable_field] = file[deliverable_field].replace("SAMPLEID", sample_id)
                file[deliverable_field] = file[deliverable_field].replace(
                    "PATHTOCASE", str(self.get_case_path(case_id=case_id))
                )
            files.append(FileDeliverable(**file))
        return PipelineDeliverables(files=files)

    def get_multiqc_json_path(self, case_id: str) -> Path:
        """Return the path of the multiqc_data.json file."""
        return Path(
            self.root_dir,
            case_id,
            MultiQC.MULTIQC,
            MultiQC.MULTIQC_DATA,
            MultiQC.MULTIQC_DATA + FileExtensions.JSON,
        )

    def get_workflow_metrics(self) -> dict:
        """Get nf-core pipeline metrics constants."""
        return {}

    def get_multiqc_json_metrics(self, case_id: str) -> list[MetricsBase]:
        """Return a list of the metrics specified in a MultiQC json file."""
        raise NotImplementedError

    def get_metric_base_list(self, sample_id: str, metrics_values: dict) -> list[MetricsBase]:
        """Return a list of MetricsBase objects for a given sample."""
        metric_base_list: list[MetricsBase] = []
        for metric_name, metric_value in metrics_values.items():
            metric_base_list.append(
                MetricsBase(
                    header=None,
                    id=sample_id,
                    input=MultiQC.MULTIQC_DATA + FileExtensions.JSON,
                    name=metric_name,
                    step=MultiQC.MULTIQC,
                    value=metric_value,
                    condition=self.get_workflow_metrics().get(metric_name, None),
                )
            )
        return metric_base_list

    @staticmethod
    def ensure_mandatory_metrics_present(metrics: list[MetricsBase]) -> None:
        return None

    def create_metrics_deliverables_content(self, case_id: str) -> dict[str, list[dict[str, Any]]]:
        """Create the content of metrics deliverables file."""
        metrics: list[MetricsBase] = self.get_multiqc_json_metrics(case_id=case_id)
        self.ensure_mandatory_metrics_present(metrics=metrics)
        return {"metrics": [metric.dict() for metric in metrics]}

    def write_metrics_deliverables(self, case_id: str, dry_run: bool = False) -> None:
        """Write <case>_metrics_deliverables.yaml file."""
        metrics_deliverables_path: Path = self.get_metrics_deliverables_path(case_id=case_id)
        content: dict = self.create_metrics_deliverables_content(case_id=case_id)
        if dry_run:
            LOG.info(
                f"Dry-run: metrics deliverables file would be written to {metrics_deliverables_path.as_posix()}"
            )
            return

        LOG.info(f"Writing metrics deliverables file to {metrics_deliverables_path.as_posix()}")
        WriteFile.write_file_from_content(
            content=content,
            file_format=FileFormat.YAML,
            file_path=metrics_deliverables_path,
        )

    def validate_qc_metrics(self, case_id: str, dry_run: bool = False) -> None:
        """Validate the information from a QC metrics deliverable file."""

        if dry_run:
            LOG.info("Dry-run: QC metrics validation would be performed")
            return

        LOG.info("Validating QC metrics")
        try:
            metrics_deliverables_path: Path = self.get_metrics_deliverables_path(case_id=case_id)
            qc_metrics_raw: dict = ReadFile.get_content_from_file(
                file_format=FileFormat.YAML, file_path=metrics_deliverables_path
            )
            MetricsDeliverablesCondition(**qc_metrics_raw)
        except MetricsQCError as error:
            LOG.error(f"QC metrics failed for {case_id}")
            self.trailblazer_api.set_analysis_status(case_id=case_id, status=AnalysisStatus.FAILED)
            self.trailblazer_api.add_comment(case_id=case_id, comment=str(error))
            raise MetricsQCError from error
        except CgError as error:
            LOG.error(f"Could not create metrics deliverables file: {error}")
            self.trailblazer_api.set_analysis_status(case_id=case_id, status=AnalysisStatus.ERROR)
            raise CgError from error
        self.trailblazer_api.set_analysis_status(case_id=case_id, status=AnalysisStatus.COMPLETED)

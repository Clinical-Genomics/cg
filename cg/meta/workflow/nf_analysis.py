import logging
import operator
from datetime import datetime
from pathlib import Path
from typing import Any, Union

from cg.store.models import Sample

from cg.constants import Pipeline
from cg.constants.constants import FileExtensions, FileFormat, WorkflowManager, MultiQC
from cg.constants.nextflow import NFX_WORK_DIR
from cg.io.yaml import write_yaml_nextflow_style
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.nf_handlers import NextflowHandler, NfTowerHandler
from cg.models.cg_config import CGConfig
from cg.models.nf_analysis import FileDeliverable, PipelineDeliverables
from cg.models.rnafusion.rnafusion import CommandArgs
from cg.utils import Process
from cg.models.deliverables.metric_deliverables import (
    MetricsBase,
    MultiqcDataJson,
)
from cg.store.models import Case, Sample
from cg.io.json import read_json
from cg.io.controller import ReadFile, WriteFile
from cg.models.deliverables.metric_deliverables import (
    MetricsDeliverablesCondition,
)
from cg.exc import CgError, MetricsQCError
from cg.constants.tb import AnalysisStatus

LOG = logging.getLogger(__name__)


class NfAnalysisAPI(AnalysisAPI):
    """Parent class for handling NF-core analyses."""

    def __init__(self, config: CGConfig, pipeline: Pipeline):
        super().__init__(config=config, pipeline=pipeline)
        self.pipeline: Pipeline = pipeline
        self.root_dir: str | None = None
        self.nfcore_pipeline_path: str | None = None
        self.references: str | None = None
        self.profile: str | None = None
        self.conda_env: str | None = None
        self.conda_binary: str | None = None
        self.tower_binary_path: str | None = None
        self.tower_pipeline: str | None = None
        self.account: str | None = None
        self.email: str | None = None
        self.compute_env: str | None = None
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

    def get_pipeline_version(self, case_id: str) -> str:
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

    @staticmethod
    def get_nextflow_config_path(nextflow_config: str | None = None) -> Path | None:
        """Path to Nextflow config file."""
        if nextflow_config:
            return Path(nextflow_config).absolute()

    def get_trailblazer_config_path(self, case_id: str) -> Path:
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

    def write_metrics_deliverables(self, case_id: str, dry_run: bool = False) -> None:
        """Write <case>_metrics_deliverables.yaml file."""
        raise NotImplementedError

    def get_log_path(self, case_id: str, pipeline: str, log: str = None) -> Path:
        """Path to NF log."""
        if log:
            return log
        launch_time: str = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
        return Path(
            self.get_case_path(case_id),
            f"{case_id}_{pipeline}_nextflow_{launch_time}",
        ).with_suffix(FileExtensions.LOG)

    def get_workdir_path(self, case_id: str, work_dir: Path | None = None) -> Path:
        """Path to NF work directory."""
        if work_dir:
            return work_dir.absolute()
        return Path(self.get_case_path(case_id), NFX_WORK_DIR)

    @staticmethod
    def extract_read_files(
        metadata: list, forward_read: bool = False, reverse_read: bool = False
    ) -> list[str]:
        """Extract a list of fastq file paths for either forward or reverse reads."""
        if forward_read and not reverse_read:
            read_direction = 1
        elif reverse_read and not forward_read:
            read_direction = 2
        else:
            raise ValueError("Either forward or reverse needs to be specified")
        sorted_metadata: list = sorted(metadata, key=operator.itemgetter("path"))
        return [d["path"] for d in sorted_metadata if d["read"] == read_direction]

    def verify_sample_sheet_exists(self, case_id: str, dry_run: bool = False) -> None:
        """Raise an error if sample sheet file is not found."""
        if not dry_run and not Path(self.get_sample_sheet_path(case_id=case_id)).exists():
            raise ValueError(f"No config file found for case {case_id}")

    def verify_deliverables_file_exists(self, case_id: str) -> None:
        """Raise an error if deliverables files file is not found."""
        if not Path(self.get_deliverables_file_path(case_id=case_id)).exists():
            raise CgError(f"No deliverables file found for case {case_id}")

    def write_params_file(self, case_id: str, pipeline_parameters: dict) -> None:
        """Write params-file for analysis."""
        LOG.debug("Writing parameters file")
        write_yaml_nextflow_style(
            content=pipeline_parameters,
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
        config_path: Path = self.get_trailblazer_config_path(case_id=case_id)
        LOG.info(f"Writing Tower ID to {config_path.as_posix()}")
        WriteFile.write_file_from_content(
            content={case_id: [tower_id]},
            file_format=FileFormat.YAML,
            file_path=config_path,
        )

    def run_analysis(
        self,
        case_id: str,
        command_args: CommandArgs,
        use_nextflow: bool,
        dry_run: bool = False,
    ) -> None:
        """Execute run analysis with given options."""
        if use_nextflow:
            self.process = Process(
                binary=self.nextflow_binary_path,
                environment=self.conda_env,
                conda_binary=self.conda_binary,
                launch_directory=self.get_case_path(case_id=case_id),
            )
            LOG.info("Pipeline will be executed using nextflow")
            parameters: list[str] = NextflowHandler.get_nextflow_run_parameters(
                case_id=case_id,
                pipeline_path=self.nfcore_pipeline_path,
                root_dir=self.root_dir,
                command_args=command_args.dict(),
            )
            self.process.export_variables(
                export=NextflowHandler.get_variables_to_export(),
            )

            command = self.process.get_command(parameters=parameters)
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
            LOG.info(f"Nextflow head job running as job {sbatch_number}")

        else:
            LOG.info("Pipeline will be executed using tower")
            if command_args.resume:
                from_tower_id: int = command_args.id
                if not from_tower_id:
                    from_tower_id: int = NfTowerHandler.get_last_tower_id(
                        case_id=case_id,
                        trailblazer_config=self.get_trailblazer_config_path(case_id=case_id),
                    )
                LOG.info(f"Pipeline will be resumed from run {from_tower_id}.")
                parameters: list[str] = NfTowerHandler.get_tower_relaunch_parameters(
                    from_tower_id=from_tower_id, command_args=command_args.dict()
                )
            else:
                parameters: list[str] = NfTowerHandler.get_tower_launch_parameters(
                    tower_pipeline=self.tower_pipeline,
                    command_args=command_args.dict(),
                )
            self.process.run_command(parameters=parameters, dry_run=dry_run)
            if self.process.stderr:
                LOG.error(self.process.stderr)
            if not dry_run:
                tower_id = NfTowerHandler.get_tower_id(stdout_lines=self.process.stdout_lines())
                self.write_trailblazer_config(case_id=case_id, tower_id=tower_id)
            LOG.info(self.process.stdout)

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

    def get_multiqc_json_metrics(
        self, case_id: str, pipeline_metrics: Union[dict, None] = None
    ) -> list[MetricsBase]:
        """Get a multiqc_data.json file and returns metrics and values formatted."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_id: str = case.links[0].sample.internal_id
        multiqc_json = MultiqcDataJson(
            **read_json(file_path=self.get_multiqc_json_path(case_id=case_id))
        )
        metrics_values: dict = {}
        for key in multiqc_json.report_general_stats_data:
            if case_id in key:
                metrics_values.update(list(key.values())[0])
                LOG.info(f"Key: {key}, Values: {list(key.values())[0]}")
        return [
            MetricsBase(
                header=None,
                id=sample_id,
                input=MultiQC.MULTIQC_DATA + FileExtensions.JSON,
                name=metric_name,
                step=MultiQC.MULTIQC,
                value=metric_value,
                condition=pipeline_metrics.get(metric_name, None),
            )
            for metric_name, metric_value in metrics_values.items()
        ]

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

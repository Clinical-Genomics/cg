import copy
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Type

from dateutil.parser import parse
from pydantic import TypeAdapter
from pydantic.v1 import ValidationError

from cg.constants import Workflow
from cg.constants.constants import (
    CaseActions,
    FileExtensions,
    FileFormat,
    GenomeVersion,
    MultiQC,
    WorkflowManager,
)
from cg.constants.gene_panel import GenePanelGenomeBuild
from cg.constants.housekeeper_tags import AlignmentFileTag
from cg.constants.nextflow import NFX_WORK_DIR
from cg.constants.nf_analysis import NfTowerStatus
from cg.constants.tb import AnalysisStatus
from cg.exc import CgError, HousekeeperStoreError, MetricsQCError
from cg.io.controller import ReadFile, WriteFile
from cg.io.json import read_json
from cg.io.txt import concat_txt, write_txt
from cg.io.yaml import read_yaml, write_yaml_nextflow_style
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.nf_handlers import NextflowHandler, NfTowerHandler
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import (
    MetricsBase,
    MetricsDeliverablesCondition,
    MultiqcDataJson,
)
from cg.models.fastq import FastqFileMeta
from cg.models.nf_analysis import (
    FileDeliverable,
    NfCommandArgs,
    WorkflowDeliverables,
    WorkflowParameters,
)
from cg.models.qc_metrics import QCMetrics
from cg.store.models import Analysis, Case, CaseSample, Sample
from cg.utils import Process

LOG = logging.getLogger(__name__)


class NfAnalysisAPI(AnalysisAPI):
    """Parent class for handling NF-core analyses."""

    def __init__(self, config: CGConfig, workflow: Workflow):
        super().__init__(workflow=workflow, config=config)
        self.workflow: Workflow = workflow
        self.root_dir: str | None = None
        self.workflow_bin_path: str | None = None
        self.references: str | None = None
        self.profile: str | None = None
        self.conda_env: str | None = None
        self.conda_binary: str | None = None
        self.platform: str | None = None
        self.params: str | None = None
        self.workflow_config_path: str | None = None
        self.resources: str | None = None
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

    @property
    def use_read_count_threshold(self) -> bool:
        """Defines whether the threshold for adequate read count should be passed for all samples
        when determining if the analysis for a case should be automatically started."""
        return True

    @property
    def sample_sheet_headers(self) -> list[str]:
        """Headers for sample sheet."""
        raise NotImplementedError

    @property
    def is_multiqc_pattern_search_exact(self) -> bool:
        """Return True if only exact pattern search is allowed to collect metrics information from MultiQC file.
        If false, pattern must be present but does not need to be exact."""
        return False

    @property
    def is_gene_panel_required(self) -> bool:
        """Return True if a gene panel needs to be created using the information in StatusDB and exporting it from Scout."""
        return False

    @property
    def is_managed_variants_required(self) -> bool:
        """Return True if a managed variant export needs to be exported it from Scout."""
        return False

    def get_profile(self, profile: str | None = None) -> str:
        """Get NF profiles."""
        return profile or self.profile

    def get_workflow_manager(self) -> str:
        """Get workflow manager from Tower."""
        return WorkflowManager.Tower.value

    def get_workflow_version(self, case_id: str) -> str:
        """Get workflow version from config."""
        return self.revision

    def get_built_workflow_parameters(
        self, case_id: str, dry_run: bool = False
    ) -> WorkflowParameters:
        """Return workflow parameters."""
        raise NotImplementedError

    def get_nextflow_config_content(self, case_id: str) -> str:
        """Return nextflow config content."""
        config_files_list: list[str] = [
            self.platform,
            self.workflow_config_path,
            self.resources,
        ]
        extra_parameters_str: list[str] = [
            self.set_cluster_options(case_id=case_id),
        ]
        return concat_txt(
            file_paths=config_files_list,
            str_content=extra_parameters_str,
        )

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

    def get_nextflow_config_path(
        self, case_id: str, nextflow_config: Path | str | None = None
    ) -> Path:
        """Path to nextflow config file."""
        if nextflow_config:
            return Path(nextflow_config).absolute()
        return Path((self.get_case_path(case_id)), f"{case_id}_nextflow_config").with_suffix(
            FileExtensions.JSON
        )

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

    def get_log_path(self, case_id: str, workflow: str) -> Path:
        """Path to NF log."""
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

    def get_gene_panels_path(self, case_id: str) -> Path:
        """Path to gene panels bed file exported from Scout."""
        return Path(self.get_case_path(case_id=case_id), "gene_panels").with_suffix(
            FileExtensions.BED
        )

    def set_cluster_options(self, case_id: str) -> str:
        return f'process.clusterOptions = "-A {self.account} --qos={self.get_slurm_qos_for_case(case_id=case_id)}"\n'

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

    def get_paired_read_paths(self, sample: Sample) -> tuple[list[str], list[str]]:
        """Returns a tuple of paired fastq file paths for the forward and reverse read."""
        sample_metadata: list[FastqFileMeta] = self.gather_file_metadata_for_sample(sample=sample)
        fastq_forward_read_paths: list[str] = self.extract_read_files(
            metadata=sample_metadata, forward_read=True
        )
        fastq_reverse_read_paths: list[str] = self.extract_read_files(
            metadata=sample_metadata, reverse_read=True
        )
        return fastq_forward_read_paths, fastq_reverse_read_paths

    def get_bam_read_file_paths(self, sample: Sample) -> list[Path]:
        """Gather BAM file path for a sample based on the BAM tag."""
        return [
            Path(hk_file.full_path)
            for hk_file in self.housekeeper_api.files(
                bundle=sample.internal_id, tags={AlignmentFileTag.BAM}
            )
        ]

    def get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        raise NotImplementedError

    def get_sample_sheet_content(self, case_id: str) -> list[list[Any]]:
        """Return formatted information required to build a sample sheet for a case.
        This contains information for all samples linked to the case."""
        sample_sheet_content: list = []
        case: Case = self.get_validated_case(case_id)
        LOG.info(f"Samples linked to case {case_id}: {len(case.links)}")
        LOG.debug("Getting sample sheet information")
        for link in case.links:
            sample_sheet_content.extend(self.get_sample_sheet_content_per_sample(case_sample=link))
        return sample_sheet_content

    def verify_sample_sheet_exists(self, case_id: str, dry_run: bool = False) -> None:
        """Raise an error if sample sheet file is not found."""
        if not dry_run and not Path(self.get_sample_sheet_path(case_id=case_id)).exists():
            raise ValueError(f"No config file found for case {case_id}")

    def verify_deliverables_file_exists(self, case_id: str) -> None:
        """Raise an error if a deliverable file is not found."""
        if not Path(self.get_deliverables_file_path(case_id=case_id)).exists():
            raise CgError(f"No deliverables file found for case {case_id}")

    def write_params_file(self, case_id: str, replaced_workflow_parameters: dict = None) -> None:
        """Write params-file for analysis."""
        LOG.debug("Writing parameters file")
        if replaced_workflow_parameters:
            write_yaml_nextflow_style(
                content=replaced_workflow_parameters,
                file_path=self.get_params_file_path(case_id=case_id),
            )
        else:
            self.get_params_file_path(case_id=case_id).touch()

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

    def create_sample_sheet(self, case_id: str, dry_run: bool) -> None:
        """Create sample sheet for a case."""
        sample_sheet_content: list[list[Any]] = self.get_sample_sheet_content(case_id=case_id)
        if not dry_run:
            self.write_sample_sheet(
                content=sample_sheet_content,
                file_path=self.get_sample_sheet_path(case_id=case_id),
                header=self.sample_sheet_headers,
            )

    def create_params_file(self, case_id: str, dry_run: bool) -> None:
        """Create parameters file for a case."""
        LOG.debug("Getting parameters information built on-the-fly")
        built_workflow_parameters: dict | None = self.get_built_workflow_parameters(
            case_id=case_id, dry_run=dry_run
        ).model_dump()
        LOG.debug("Adding parameters from the pipeline config file if it exist")

        yaml_params: dict = (
            read_yaml(self.params) if hasattr(self, "params") and self.params else {}
        )

        # Check for duplicate keys
        duplicate_keys = set(built_workflow_parameters.keys()) & set(yaml_params.keys())
        if duplicate_keys:
            raise ValueError(f"Duplicate parameter keys found: {duplicate_keys}")
        workflow_parameters: dict = built_workflow_parameters | (yaml_params)
        replaced_workflow_parameters: dict = self.replace_values_in_params_file(
            workflow_parameters=workflow_parameters
        )
        if not dry_run:
            self.write_params_file(
                case_id=case_id, replaced_workflow_parameters=replaced_workflow_parameters
            )

    def replace_values_in_params_file(self, workflow_parameters: dict) -> dict:
        replaced_workflow_parameters = copy.deepcopy(workflow_parameters)
        """Iterate through the dictionary until all placeholders are replaced with the corresponding value from the dictionary"""
        while True:
            resolved: bool = True
            for key, value in replaced_workflow_parameters.items():
                new_value: str | int = self.replace_params_placeholders(value, workflow_parameters)
                if new_value != value:
                    resolved = False
                    replaced_workflow_parameters[key] = new_value
            if resolved:
                break
        return replaced_workflow_parameters

    def replace_params_placeholders(self, value: str | int, workflow_parameters: dict) -> str:
        """Replace values marked as placeholders with values from the given dictionary"""
        if isinstance(value, str):
            placeholders: list[str] = re.findall(r"{{\s*([^{}\s]+)\s*}}", value)
            for placeholder in placeholders:
                if placeholder in workflow_parameters:
                    value = value.replace(
                        f"{{{{{placeholder}}}}}", str(workflow_parameters[placeholder])
                    )
        return value

    def create_nextflow_config(self, case_id: str, dry_run: bool = False) -> None:
        """Create nextflow config file."""
        if content := self.get_nextflow_config_content(case_id=case_id):
            LOG.debug("Writing nextflow config file")
            if not dry_run:
                write_txt(
                    content=content,
                    file_path=self.get_nextflow_config_path(case_id=case_id),
                )

    def create_gene_panel(self, case_id: str, dry_run: bool) -> None:
        """Create and write an aggregated gene panel file exported from Scout."""
        LOG.info("Creating gene panel file")
        bed_lines: list[str] = self.get_gene_panel(case_id=case_id, dry_run=dry_run)
        if dry_run:
            bed_lines: str = "\n".join(bed_lines)
            LOG.debug(f"{bed_lines}")
            return
        self.write_panel(case_id=case_id, content=bed_lines)

    def config_case(self, case_id: str, dry_run: bool):
        """Create directory and config files required by a workflow for a case."""
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
        self.status_db.verify_case_exists(case_internal_id=case_id)
        self.create_case_directory(case_id=case_id, dry_run=dry_run)
        self.create_sample_sheet(case_id=case_id, dry_run=dry_run)
        self.create_params_file(case_id=case_id, dry_run=dry_run)
        self.create_nextflow_config(case_id=case_id, dry_run=dry_run)
        if self.is_gene_panel_required:
            self.create_gene_panel(case_id=case_id, dry_run=dry_run)
        if self.is_managed_variants_required:
            vcf_lines: list[str] = self.get_managed_variants(case_id=case_id)
            if dry_run:
                for line in vcf_lines:
                    LOG.debug(line)
            else:
                self.write_managed_variants(case_id=case_id, content=vcf_lines)

    def _run_analysis_with_nextflow(
        self, case_id: str, command_args: NfCommandArgs, dry_run: bool
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
            workflow_bin_path=self.workflow_bin_path,
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
        self, case_id: str, command_args: NfCommandArgs, dry_run: bool
    ) -> str | None:
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
            return tower_id
        LOG.info(self.process.stdout)

    def get_command_args(
        self,
        case_id: str,
        work_dir: str,
        from_start: bool,
        profile: str,
        config: str,
        params_file: str | None,
        revision: str,
        compute_env: str,
        nf_tower_id: str | None,
        stub_run: bool,
    ) -> NfCommandArgs:
        command_args: NfCommandArgs = NfCommandArgs(
            **{
                "log": self.get_log_path(case_id=case_id, workflow=self.workflow),
                "work_dir": self.get_workdir_path(case_id=case_id, work_dir=work_dir),
                "resume": not from_start,
                "profile": self.get_profile(profile=profile),
                "config": self.get_nextflow_config_path(case_id=case_id, nextflow_config=config),
                "params_file": self.get_params_file_path(case_id=case_id, params_file=params_file),
                "name": case_id,
                "compute_env": compute_env or self.get_compute_env(case_id=case_id),
                "revision": revision or self.revision,
                "wait": NfTowerStatus.SUBMITTED,
                "id": nf_tower_id,
                "stub_run": stub_run,
            }
        )
        return command_args

    def run_nextflow_analysis(
        self,
        case_id: str,
        use_nextflow: bool,
        work_dir: str,
        from_start: bool,
        profile: str,
        config: str,
        params_file: str | None,
        revision: str,
        compute_env: str,
        stub_run: bool,
        nf_tower_id: str | None = None,
        dry_run: bool = False,
    ) -> None:
        """Prepare and start run analysis: check existence of all input files generated by config-case and sync with trailblazer."""
        self.status_db.verify_case_exists(case_internal_id=case_id)

        command_args = self.get_command_args(
            case_id=case_id,
            work_dir=work_dir,
            from_start=from_start,
            profile=profile,
            config=config,
            params_file=params_file,
            revision=revision,
            compute_env=compute_env,
            nf_tower_id=nf_tower_id,
            stub_run=stub_run,
        )

        try:
            self.verify_sample_sheet_exists(case_id=case_id, dry_run=dry_run)
            self.check_analysis_ongoing(case_id=case_id)
            LOG.info(f"Running analysis for {case_id}")
            tower_workflow_id: str | None = self.run_analysis(
                case_id=case_id,
                command_args=command_args,
                use_nextflow=use_nextflow,
                dry_run=dry_run,
            )
            if not dry_run:
                self.on_analysis_started(case_id=case_id, tower_workflow_id=tower_workflow_id)
        except FileNotFoundError as error:
            LOG.error(f"Could not resume analysis: {error}")
            raise FileNotFoundError
        except ValueError as error:
            LOG.error(f"Could not run analysis: {error}")
            raise ValueError
        except CgError as error:
            LOG.error(f"Could not run analysis: {error}")
            raise CgError

    def run_analysis(
        self,
        case_id: str,
        command_args: NfCommandArgs,
        use_nextflow: bool,
        dry_run: bool = False,
    ) -> str | None:
        """Execute run analysis with given options."""
        if use_nextflow:
            self._run_analysis_with_nextflow(
                case_id=case_id,
                command_args=command_args,
                dry_run=dry_run,
            )
        else:
            return self._run_analysis_with_tower(
                case_id=case_id,
                command_args=command_args,
                dry_run=dry_run,
            )

    def get_deliverables_template_content(self) -> list[dict[str, str]]:
        """Return deliverables file template content."""
        LOG.debug("Getting deliverables file template content")
        return ReadFile.get_content_from_file(
            file_format=FileFormat.YAML,
            file_path=self.get_bundle_filenames_path(),
        )

    @staticmethod
    def get_bundle_filenames_path() -> Path:
        """Return bundle filenames path."""
        raise NotImplementedError

    @staticmethod
    def get_formatted_file_deliverable(
        file_template: dict[str | None, str | None],
        case_id: str,
        sample_id: str,
        sample_name: str,
        case_path: str,
    ) -> FileDeliverable:
        """Return the formatted file deliverable with the case and sample attributes."""
        deliverables = file_template.copy()
        for deliverable_field, deliverable_value in file_template.items():
            if deliverable_value is None:
                continue
            deliverables[deliverable_field] = (
                deliverables[deliverable_field]
                .replace("CASEID", case_id)
                .replace("SAMPLEID", sample_id)
                .replace("SAMPLENAME", sample_name)
                .replace("PATHTOCASE", case_path)
            )
            LOG.debug(deliverables[deliverable_field])
        return FileDeliverable(**deliverables)

    def get_deliverables_for_sample(
        self, sample: Sample, case_id: str, template: list[dict[str, str]]
    ) -> list[FileDeliverable]:
        """Return a list of FileDeliverables for each sample."""
        sample_id: str = sample.internal_id
        sample_name: str = sample.name
        case_path = str(self.get_case_path(case_id=case_id))
        files: list[FileDeliverable] = []
        for file in template:
            files.append(
                self.get_formatted_file_deliverable(
                    file_template=file,
                    case_id=case_id,
                    sample_id=sample_id,
                    sample_name=sample_name,
                    case_path=case_path,
                )
            )
        return files

    def get_deliverables_for_case(self, case_id: str) -> WorkflowDeliverables:
        """Return workflow deliverables for a given case."""
        deliverable_template: list[dict] = self.get_deliverables_template_content()
        samples: list[Sample] = self.status_db.get_samples_by_case_id(case_id=case_id)
        files: list[FileDeliverable] = []

        for sample in samples:
            bundles_per_sample = self.get_deliverables_for_sample(
                sample=sample, case_id=case_id, template=deliverable_template
            )
            files.extend(bundle for bundle in bundles_per_sample if bundle not in files)
        return WorkflowDeliverables(files=files)

    def get_multiqc_json_path(self, case_id: str) -> Path:
        """Return the path of the multiqc_data.json file."""
        return Path(
            self.root_dir,
            case_id,
            MultiQC.MULTIQC,
            MultiQC.MULTIQC_DATA,
            MultiQC.MULTIQC_DATA + FileExtensions.JSON,
        )

    def get_workflow_metrics(self, metric_id: str) -> dict:
        """Get nf-core workflow metrics constants."""
        return {}

    def get_multiqc_search_patterns(self, case_id: str) -> dict:
        """Return search patterns for MultiQC. Each key is a search pattern and each value
        corresponds to the metric ID to set in the metrics deliverables file.
        Multiple search patterns can be added. Ideally, used patterns should be sample ids, e.g.
        {sample_id_1: sample_id_1, sample_id_2: sample_id_2}."""
        sample_ids: Iterator[str] = self.status_db.get_sample_ids_by_case_id(case_id)
        return {sample_id: sample_id for sample_id in sample_ids}

    @staticmethod
    def get_deduplicated_metrics(metrics: list[MetricsBase]) -> list[MetricsBase]:
        """Return deduplicated metrics based on metric ID and name. If duplicated entries are found
        only the first one will be kept."""
        deduplicated_metric_id_name = set([])
        deduplicated_metrics: list = []
        for metric in metrics:
            if (metric.id, metric.name) not in deduplicated_metric_id_name:
                deduplicated_metric_id_name.add((metric.id, metric.name))
                deduplicated_metrics.append(metric)
        return deduplicated_metrics

    def get_multiqc_data_json(self, case_id: str) -> MultiqcDataJson:
        return MultiqcDataJson(**read_json(file_path=self.get_multiqc_json_path(case_id=case_id)))

    def get_multiqc_json_metrics(self, case_id: str) -> list[MetricsBase]:
        """Return a list of the metrics specified in a MultiQC json file."""
        multiqc_json: MultiqcDataJson = self.get_multiqc_data_json(case_id=case_id)
        metrics = []
        for search_pattern, metric_id in self.get_multiqc_search_patterns(case_id=case_id).items():
            metrics_for_pattern: list[MetricsBase] = (
                self.get_metrics_from_multiqc_json_with_pattern(
                    search_pattern=search_pattern,
                    multiqc_json=multiqc_json,
                    metric_id=metric_id,
                    exact_match=self.is_multiqc_pattern_search_exact,
                )
            )
            metrics.extend(metrics_for_pattern)
        metrics = self.get_deduplicated_metrics(metrics=metrics)
        return metrics

    @staticmethod
    def _is_pattern_found(pattern: str, text: str, exact_match: bool) -> bool:
        if exact_match:
            is_pattern_found: bool = pattern == text
        else:
            is_pattern_found: bool = pattern in text
        return is_pattern_found

    def get_metrics_from_multiqc_json_with_pattern(
        self,
        search_pattern: str,
        multiqc_json: MultiqcDataJson,
        metric_id: str,
        exact_match: bool = False,
    ) -> list[MetricsBase]:
        """Parse a MultiqcDataJson and returns a list of metrics."""
        metrics: list[MetricsBase] = []
        for section in multiqc_json.report_general_stats_data:
            for subsection, metrics_dict in section.items():
                if self._is_pattern_found(
                    pattern=search_pattern, text=subsection, exact_match=exact_match
                ):
                    for metric_name, metric_value in metrics_dict.items():
                        metric: MetricsBase = self.get_multiqc_metric(
                            metric_name=metric_name, metric_value=metric_value, metric_id=metric_id
                        )
                        metrics.append(metric)
        return metrics

    def get_multiqc_metric(
        self, metric_name: str, metric_value: str | int | float, metric_id: str
    ) -> MetricsBase:
        """Return a MetricsBase object for a given metric."""
        return MetricsBase(
            header=None,
            id=metric_id,
            input=MultiQC.MULTIQC_DATA + FileExtensions.JSON,
            name=metric_name,
            step=MultiQC.MULTIQC,
            value=metric_value,
            condition=self.get_workflow_metrics(metric_id).get(metric_name, None),
        )

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
            LOG.error(f"QC metrics failed for {case_id}, with: {error}")
            self.trailblazer_api.set_analysis_status(case_id=case_id, status=AnalysisStatus.FAILED)
            samples = self.status_db.get_samples_by_case_id(case_id=case_id)
            for sample in samples:
                trailblazer_comment = str(error).replace(
                    f"{sample.internal_id} - ", f"{sample.name} ({sample.internal_id}) - "
                )
            self.trailblazer_api.add_comment(case_id=case_id, comment=trailblazer_comment)
            raise MetricsQCError from error
        except CgError as error:
            LOG.error(f"Could not create metrics deliverables file: {error}")
            self.trailblazer_api.set_analysis_status(case_id=case_id, status=AnalysisStatus.ERROR)
            raise CgError from error
        self.trailblazer_api.set_analysis_status(case_id=case_id, status=AnalysisStatus.COMPLETED)

    def metrics_deliver(self, case_id: str, dry_run: bool):
        """Create and validate a metrics deliverables file for given case id."""
        self.status_db.verify_case_exists(case_internal_id=case_id)
        self.write_metrics_deliverables(case_id=case_id, dry_run=dry_run)
        self.validate_qc_metrics(case_id=case_id, dry_run=dry_run)

    def report_deliver(self, case_id: str, dry_run: bool = False, force: bool = False) -> None:
        """Write deliverables file."""
        self.status_db.verify_case_exists(case_id)
        self.trailblazer_api.verify_latest_analysis_is_completed(case_id=case_id, force=force)
        if dry_run:
            LOG.info(f"Dry-run: Would have created delivery files for case {case_id}")
            return
        workflow_content: WorkflowDeliverables = self.get_deliverables_for_case(case_id=case_id)
        self.write_deliverables_file(
            deliverables_content=workflow_content.model_dump(),
            file_path=self.get_deliverables_file_path(case_id=case_id),
        )
        LOG.info(
            f"Writing deliverables file in {self.get_deliverables_file_path(case_id=case_id).as_posix()}"
        )

    def store_analysis_housekeeper(
        self, case_id: str, comment: str | None = None, dry_run: bool = False, force: bool = False
    ) -> None:
        """
        Store a finished Nextflow analysis in Housekeeper and StatusDB.

        Raises:
            HousekeeperStoreError: If the deliverables file is malformed or if the bundle could not be stored.
        """
        try:
            self.status_db.verify_case_exists(case_id)
            self.trailblazer_api.verify_latest_analysis_is_completed(case_id=case_id, force=force)
            self.verify_deliverables_file_exists(case_id)
            self.upload_bundle_housekeeper(case_id=case_id, dry_run=dry_run, force=force)
            self.update_analysis_as_completed_statusdb(
                case_id=case_id, comment=comment, dry_run=dry_run, force=force
            )
            self.set_statusdb_action(case_id=case_id, action=None, dry_run=dry_run)
        except ValidationError as error:
            raise HousekeeperStoreError(f"Deliverables file is malformed: {error}")
        except Exception as error:
            self.housekeeper_api.rollback()
            self.status_db.session.rollback()
            raise HousekeeperStoreError(
                f"Could not store bundle in Housekeeper and StatusDB: {error}"
            )

    def store(
        self, case_id: str, comment: str | None = None, dry_run: bool = False, force: bool = False
    ):
        """Generate deliverable files for a case and store in Housekeeper if they
        pass QC metrics checks."""
        is_latest_analysis_qc: bool = self.trailblazer_api.is_latest_analysis_qc(case_id)
        is_latest_analysis_completed: bool = self.trailblazer_api.is_latest_analysis_completed(
            case_id
        )
        if not is_latest_analysis_qc and not is_latest_analysis_completed and not force:
            LOG.error(
                "Case not stored. Trailblazer status must be either QC or COMPLETE to be able to store"
            )
            raise ValueError

        if (
            is_latest_analysis_qc
            or not self.get_metrics_deliverables_path(case_id=case_id).exists()
            and not force
        ):
            LOG.info(f"Generating metrics file and performing QC checks for {case_id}")
            self.metrics_deliver(case_id=case_id, dry_run=dry_run)
        LOG.info(f"Storing analysis for {case_id}")
        self.report_deliver(case_id=case_id, dry_run=dry_run, force=force)
        self.store_analysis_housekeeper(
            case_id=case_id, comment=comment, dry_run=dry_run, force=force
        )

    def get_cases_to_store(self) -> list[Case]:
        """Return cases where analysis finished successfully,
        and is ready to be stored in Housekeeper."""
        return [
            case
            for case in self.status_db.get_running_cases_in_workflow(workflow=self.workflow)
            if self.trailblazer_api.is_latest_analysis_completed(case_id=case.internal_id)
            or self.trailblazer_api.is_latest_analysis_qc(case_id=case.internal_id)
        ]

    def get_genome_build(self, case_id: str) -> GenomeVersion:
        raise NotImplementedError

    def get_gene_panel_genome_build(self, case_id: str) -> GenePanelGenomeBuild:
        """Return build version of the gene panel for a case."""
        reference_genome: GenomeVersion = self.get_genome_build(case_id=case_id)
        try:
            return getattr(GenePanelGenomeBuild, reference_genome)
        except AttributeError as error:
            raise CgError(
                f"Reference {reference_genome} has no associated genome build for panels: {error}"
            ) from error

    def get_gene_panel(self, case_id: str, dry_run: bool = False) -> list[str]:
        """Create and return the aggregated gene panel file."""
        return self._get_gene_panel(
            case_id=case_id,
            genome_build=self.get_gene_panel_genome_build(case_id=case_id),
            dry_run=dry_run,
        )

    def parse_analysis(
        self, qc_metrics_raw: list[MetricsBase], qc_metrics_model: Type[QCMetrics], **kwargs
    ) -> NextflowAnalysis:
        """Parse Nextflow output analysis files and return an analysis model."""
        sample_metrics: dict[str, dict] = {}
        for metric in qc_metrics_raw:
            try:
                sample_metrics[metric.id].update({metric.name.lower(): metric.value})
            except KeyError:
                sample_metrics[metric.id] = {metric.name.lower(): metric.value}
        pydantic_parser = TypeAdapter(dict[str, qc_metrics_model])
        return NextflowAnalysis(sample_metrics=pydantic_parser.validate_python(sample_metrics))

    def get_latest_metadata(self, case_id: str) -> NextflowAnalysis:
        """Return analysis output of a Nextflow case."""
        qc_metrics: list[MetricsBase] = self.get_multiqc_json_metrics(case_id)
        return self.parse_analysis(qc_metrics_raw=qc_metrics)

    def clean_past_run_dirs(self, before_date: str, skip_confirmation: bool = False) -> None:
        """Clean past run directories"""
        before_date: datetime = parse(before_date)
        analyses_to_clean: list[Analysis] = self.get_analyses_to_clean(before_date)
        LOG.info(f"Cleaning {len(analyses_to_clean)} analyses created before {before_date}")

        for analysis in analyses_to_clean:
            case_id = analysis.case.internal_id
            case_path = self.get_case_path(case_id)
            try:
                LOG.info(f"Cleaning output for {case_id}")
                self.clean_run_dir(
                    case_id=case_id, skip_confirmation=skip_confirmation, case_path=case_path
                )
            except FileNotFoundError:
                continue
            except Exception as error:
                LOG.error(f"Failed to clean directories for case {case_id} - {repr(error)}")
        LOG.info(f"Done cleaning {self.workflow} output")

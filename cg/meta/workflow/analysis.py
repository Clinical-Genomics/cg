import datetime as dt
import logging
import os
import shutil
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Union

import click
from housekeeper.store.models import Bundle, Version

from cg.apps.environ import environ_email
from cg.constants import (
    CASE_ACTIONS,
    EXIT_FAIL,
    EXIT_SUCCESS,
    Pipeline,
    Priority,
    SequencingFileTag,
)
from cg.constants.archiving import ArchiveLocations
from cg.constants.constants import AnalysisType, CaseActions, WorkflowManager
from cg.constants.priority import PRIORITY_TO_SLURM_QOS
from cg.exc import AnalysisNotReadyError, BundleAlreadyAddedError, CgDataError, CgError
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.meta import MetaAPI
from cg.meta.workflow.fastq import FastqHandler
from cg.models.analysis import AnalysisModel
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, BedVersion, Case, CaseSample, Sample

LOG = logging.getLogger(__name__)


class AnalysisAPI(MetaAPI):
    """
    Parent class containing all methods that are either shared or overridden by other workflow APIs
    """

    def __init__(self, pipeline: Pipeline, config: CGConfig):
        super().__init__(config=config)
        self.pipeline = pipeline
        self._process = None

    @property
    def root(self):
        raise NotImplementedError

    @property
    def use_read_count_threshold(self) -> bool:
        """Defines whether the threshold for adequate read count should be passed for all samples
        when determining if the analysis for a case should be automatically started"""
        return False

    @property
    def process(self):
        raise NotImplementedError

    @property
    def fastq_handler(self):
        return FastqHandler

    @staticmethod
    def get_help(context):
        """
        If no argument is passed, print help text
        """
        if context.invoked_subcommand is None:
            click.echo(context.get_help())

    def verify_deliverables_file_exists(self, case_id: str) -> None:
        if not Path(self.get_deliverables_file_path(case_id=case_id)).exists():
            raise CgError(f"No deliverables file found for case {case_id}")

    def verify_case_config_file_exists(self, case_id: str) -> None:
        if not Path(self.get_case_config_path(case_id=case_id)).exists():
            raise CgError(f"No config file found for case {case_id}")

    def check_analysis_ongoing(self, case_id: str) -> None:
        if self.trailblazer_api.is_latest_analysis_ongoing(case_id=case_id):
            LOG.warning(f"{case_id} : analysis is still ongoing - skipping")
            raise CgError(f"Analysis still ongoing in Trailblazer for case {case_id}")

    def verify_case_path_exists(self, case_id: str) -> None:
        """Check if case path exists."""
        if not self.get_case_path(case_id=case_id).exists():
            LOG.info(f"No working directory for {case_id} exists")
            raise FileNotFoundError(f"No working directory for {case_id} exists")

    def get_priority_for_case(self, case_id: str) -> int:
        """Get priority from the status db case priority"""
        case_obj: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        return case_obj.priority.value or Priority.research

    def get_slurm_qos_for_case(self, case_id: str) -> str:
        """Get Quality of service (SLURM QOS) for the case."""
        priority: int = self.get_priority_for_case(case_id=case_id)
        return PRIORITY_TO_SLURM_QOS[priority]

    def get_workflow_manager(self) -> str:
        """Get workflow manager for a given pipeline."""
        return WorkflowManager.Slurm.value

    def get_case_path(self, case_id: str) -> Union[list[Path], Path]:
        """Path to case working directory."""
        raise NotImplementedError

    def get_case_config_path(self, case_id) -> Path:
        """Path to case config file"""
        raise NotImplementedError

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        """Path to Trailblazer job id file"""
        raise NotImplementedError

    def get_sample_name_from_lims_id(self, lims_id: str) -> str:
        """Retrieve sample name provided by customer for specific sample"""
        sample: Sample = self.status_db.get_sample_by_internal_id(internal_id=lims_id)
        return sample.name

    def link_fastq_files(self, case_id: str, dry_run: bool = False) -> None:
        """
        Links fastq files from Housekeeper to case working directory
        """
        raise NotImplementedError

    def get_bundle_deliverables_type(self, case_id: str) -> Optional[str]:
        return None

    @staticmethod
    def get_application_type(sample_obj: Sample) -> str:
        """
        Gets application type for sample. Only application types supported by trailblazer (or other)
        are valid outputs.
        """
        prep_category: str = sample_obj.prep_category
        if prep_category and prep_category.lower() in {
            AnalysisType.TARGETED_GENOME_SEQUENCING,
            AnalysisType.WHOLE_EXOME_SEQUENCING,
            AnalysisType.WHOLE_GENOME_SEQUENCING,
            AnalysisType.WHOLE_TRANSCRIPTOME_SEQUENCING,
        }:
            return prep_category.lower()
        return AnalysisType.OTHER

    def upload_bundle_housekeeper(self, case_id: str, dry_run: bool = False) -> None:
        """Storing bundle data in Housekeeper for CASE_ID"""
        LOG.info(f"Storing bundle data in Housekeeper for {case_id}")
        bundle_data: dict = self.get_hermes_transformed_deliverables(case_id)
        bundle_result: tuple[Bundle, Version] = self.housekeeper_api.add_bundle(
            bundle_data=bundle_data
        )
        if not bundle_result:
            LOG.info("Bundle already added to Housekeeper!")
            raise BundleAlreadyAddedError("Bundle already added to Housekeeper!")
        bundle_object, bundle_version = bundle_result
        if dry_run:
            LOG.info("Dry-run: Housekeeper changes will not be commited")
            LOG.info(
                "The following files would be stored:\n%s",
                "\n".join([f["path"] for f in bundle_data["files"]]),
            )
            return
        self.housekeeper_api.include(bundle_version)
        self.housekeeper_api.add_commit(bundle_object)
        self.housekeeper_api.add_commit(bundle_version)
        LOG.info(
            f"Analysis successfully stored in Housekeeper: {case_id} : {bundle_version.created_at}"
        )

    def upload_bundle_statusdb(self, case_id: str, dry_run: bool = False) -> None:
        """Storing analysis bundle in StatusDB for CASE_ID"""

        LOG.info(f"Storing analysis in StatusDB for {case_id}")
        case_obj: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        analysis_start: dt.datetime = self.get_bundle_created_date(case_id=case_id)
        pipeline_version: str = self.get_pipeline_version(case_id=case_id)
        new_analysis: Case = self.status_db.add_analysis(
            pipeline=self.pipeline,
            version=pipeline_version,
            started_at=analysis_start,
            completed_at=dt.datetime.now(),
            primary=(len(case_obj.analyses) == 0),
        )
        new_analysis.case = case_obj
        if dry_run:
            LOG.info("Dry-run: StatusDB changes will not be commited")
            return
        self.status_db.session.add(new_analysis)
        self.status_db.session.commit()
        LOG.info(f"Analysis successfully stored in StatusDB: {case_id} : {analysis_start}")

    def get_deliverables_file_path(self, case_id: str) -> Path:
        raise NotImplementedError

    def get_analysis_finish_path(self, case_id: str) -> Path:
        raise NotImplementedError

    def add_pending_trailblazer_analysis(self, case_id: str) -> None:
        self.check_analysis_ongoing(case_id=case_id)
        self.trailblazer_api.mark_analyses_deleted(case_id=case_id)
        self.trailblazer_api.add_pending_analysis(
            case_id=case_id,
            email=environ_email(),
            analysis_type=self.get_application_type(
                self.status_db.get_case_by_internal_id(internal_id=case_id).links[0].sample
            ),
            out_dir=self.get_trailblazer_config_path(case_id=case_id).parent.as_posix(),
            config_path=self.get_trailblazer_config_path(case_id=case_id).as_posix(),
            slurm_quality_of_service=self.get_slurm_qos_for_case(case_id=case_id),
            data_analysis=str(self.pipeline),
            ticket=self.status_db.get_latest_ticket_from_case(case_id),
            workflow_manager=self.get_workflow_manager(),
        )

    def get_hermes_transformed_deliverables(self, case_id: str) -> dict:
        return self.hermes_api.create_housekeeper_bundle(
            bundle_name=case_id,
            deliverables=self.get_deliverables_file_path(case_id=case_id),
            pipeline=str(self.pipeline),
            analysis_type=self.get_bundle_deliverables_type(case_id),
            created=self.get_bundle_created_date(case_id),
        ).model_dump()

    def get_bundle_created_date(self, case_id: str) -> dt.datetime:
        return self.get_date_from_file_path(self.get_deliverables_file_path(case_id=case_id))

    def get_pipeline_version(self, case_id: str) -> str:
        """
        Calls the pipeline to get the pipeline version number. If fails, returns a placeholder value instead.
        """
        try:
            self.process.run_command(["--version"])
            return list(self.process.stdout_lines())[0].split()[-1]
        except (Exception, CalledProcessError):
            LOG.warning("Could not retrieve %s workflow version!", self.pipeline)
            return "0.0.0"

    def set_statusdb_action(
        self, case_id: str, action: Optional[str], dry_run: bool = False
    ) -> None:
        """
        Set one of the allowed actions on a case in StatusDB.
        """
        if dry_run:
            LOG.info(f"Dry-run: Action {action} would be set for case {case_id}")
            return
        if action in [None, *CASE_ACTIONS]:
            case_obj: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
            case_obj.action = action
            self.status_db.session.commit()
            LOG.info("Action %s set for case %s", action, case_id)
            return
        LOG.warning(
            f"Action '{action}' not permitted by StatusDB and will not be set for case {case_id}"
        )

    def get_analyses_to_clean(self, before: dt.datetime) -> list[Analysis]:
        analyses_to_clean = self.status_db.get_analyses_to_clean(
            pipeline=self.pipeline, before=before
        )
        return analyses_to_clean

    def get_cases_to_analyze(self) -> list[Case]:
        return self.status_db.cases_to_analyze(
            pipeline=self.pipeline, threshold=self.use_read_count_threshold
        )

    def get_cases_to_store(self) -> list[Case]:
        """Return cases where analysis finished successfully,
        and is ready to be stored in Housekeeper."""
        return [
            case
            for case in self.status_db.get_running_cases_in_pipeline(pipeline=self.pipeline)
            if self.trailblazer_api.is_latest_analysis_completed(case_id=case.internal_id)
        ]

    def get_cases_to_qc(self) -> list[Case]:
        """Return cases where analysis finished successfully,
        and is ready for QC metrics checks."""
        return [
            case
            for case in self.status_db.get_running_cases_in_pipeline(pipeline=self.pipeline)
            if self.trailblazer_api.is_latest_analysis_qc(case_id=case.internal_id)
        ]

    def get_sample_fastq_destination_dir(self, case: Case, sample: Sample):
        """Return the path to the FASTQ destination directory."""
        raise NotImplementedError

    def gather_file_metadata_for_sample(self, sample_obj: Sample) -> list[dict]:
        return [
            self.fastq_handler.parse_file_data(file_obj.full_path)
            for file_obj in self.housekeeper_api.files(
                bundle=sample_obj.internal_id, tags=["fastq"]
            )
        ]

    def link_fastq_files_for_sample(
        self, case_obj: Case, sample_obj: Sample, concatenate: bool = False
    ) -> None:
        """
        Link FASTQ files for a sample to working directory.
        If pipeline input requires concatenated fastq, files can also be concatenated
        """
        linked_reads_paths = {1: [], 2: []}
        concatenated_paths = {1: "", 2: ""}
        files: list[dict] = self.gather_file_metadata_for_sample(sample_obj=sample_obj)
        sorted_files = sorted(files, key=lambda k: k["path"])
        fastq_dir = self.get_sample_fastq_destination_dir(case=case_obj, sample=sample_obj)
        fastq_dir.mkdir(parents=True, exist_ok=True)

        for fastq_data in sorted_files:
            fastq_path = Path(fastq_data["path"])
            fastq_name = self.fastq_handler.create_fastq_name(
                lane=fastq_data["lane"],
                flowcell=fastq_data["flowcell"],
                sample=sample_obj.internal_id,
                read=fastq_data["read"],
                undetermined=fastq_data["undetermined"],
                meta=self.get_additional_naming_metadata(sample_obj),
            )
            destination_path: Path = fastq_dir / fastq_name
            linked_reads_paths[fastq_data["read"]].append(destination_path)
            concatenated_paths[
                fastq_data["read"]
            ] = f"{fastq_dir}/{self.fastq_handler.get_concatenated_name(fastq_name)}"

            if not destination_path.exists():
                LOG.info(f"Linking: {fastq_path} -> {destination_path}")
                destination_path.symlink_to(fastq_path)
            else:
                LOG.warning(f"Destination path already exists: {destination_path}")

        if not concatenate:
            return

        LOG.info("Concatenation in progress for sample %s.", sample_obj.internal_id)
        for read, value in linked_reads_paths.items():
            self.fastq_handler.concatenate(linked_reads_paths[read], concatenated_paths[read])
            self.fastq_handler.remove_files(value)

    def get_target_bed_from_lims(self, case_id: str) -> Optional[str]:
        """Get target bed filename from LIMS."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample: Sample = case.links[0].sample
        if sample.from_sample:
            sample: Sample = self.status_db.get_sample_by_internal_id(
                internal_id=sample.from_sample
            )
        target_bed_shortname: str = self.lims_api.capture_kit(lims_id=sample.internal_id)
        if not target_bed_shortname:
            return None
        bed_version: Optional[BedVersion] = self.status_db.get_bed_version_by_short_name(
            bed_version_short_name=target_bed_shortname
        )
        if not bed_version:
            raise CgDataError(f"Bed-version {target_bed_shortname} does not exist")
        return bed_version.filename

    def decompression_running(self, case_id: str) -> None:
        """Check if decompression is running for a case"""
        is_decompression_running: bool = self.prepare_fastq_api.is_spring_decompression_running(
            case_id
        )
        if not is_decompression_running:
            LOG.warning(
                "Decompression can not be started for %s",
                case_id,
            )
            return
        LOG.info(
            "Decompression is running for %s, analysis will be started when decompression is done",
            case_id,
        )
        self.set_statusdb_action(case_id=case_id, action="analyze")

    def decompress_case(self, case_id: str, dry_run: bool) -> None:
        """Decompress all possible fastq files for all samples in a case"""
        LOG.info(
            "The analysis for %s could not start, decompression is needed",
            case_id,
        )
        decompression_possible: bool = (
            self.prepare_fastq_api.can_at_least_one_sample_be_decompressed(case_id)
        )
        if not decompression_possible:
            self.decompression_running(case_id=case_id)
            return
        case_obj: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        link: CaseSample
        any_decompression_started = False
        for link in case_obj.links:
            sample_id: str = link.sample.internal_id
            if dry_run:
                LOG.info(
                    f"This is a dry run, therefore decompression for {sample_id} won't be started"
                )
                continue
            decompression_started: bool = self.prepare_fastq_api.compress_api.decompress_spring(
                sample_id
            )
            if decompression_started:
                any_decompression_started = True

        if not any_decompression_started:
            LOG.warning("Decompression failed to start for %s", case_id)
            return
        if not dry_run:
            self.set_statusdb_action(case_id=case_id, action="analyze")
        LOG.info("Decompression started for %s", case_id)

    def resolve_decompression(self, case_id: str, dry_run: bool) -> None:
        """
        Decompresses a case if needed and adds new fastq files to Housekeeper.
        """
        if self.prepare_fastq_api.is_spring_decompression_needed(case_id):
            self.decompress_case(case_id=case_id, dry_run=dry_run)
            return

        if self.prepare_fastq_api.is_spring_decompression_running(case_id):
            self.set_statusdb_action(case_id=case_id, action=CaseActions.ANALYZE)
            return

        self.prepare_fastq_api.add_decompressed_fastq_files_to_housekeeper(case_id)

    @staticmethod
    def get_date_from_file_path(file_path: Path) -> dt.datetime.date:
        """
        Get date from deliverables path using date created metadata.
        """
        return dt.datetime.fromtimestamp(int(os.path.getctime(file_path)))

    def get_additional_naming_metadata(self, sample_obj: Sample) -> Optional[str]:
        return None

    def get_latest_metadata(self, case_id: str) -> AnalysisModel:
        """Get the latest metadata of a specific case"""

        raise NotImplementedError

    def parse_analysis(
        self, config_raw: dict, qc_metrics_raw: dict, sample_info_raw: dict
    ) -> AnalysisModel:
        """Parses output analysis files"""

        raise NotImplementedError

    def clean_analyses(self, case_id: str) -> None:
        """Add a cleaned at date for all analyses related to a case."""
        analyses: list = self.status_db.get_case_by_internal_id(internal_id=case_id).analyses
        LOG.info(f"Adding a cleaned at date for case {case_id}")
        for analysis_obj in analyses:
            analysis_obj.cleaned_at = analysis_obj.cleaned_at or dt.datetime.now()
            self.status_db.session.commit()

    def clean_run_dir(self, case_id: str, yes: bool, case_path: Union[list[Path], Path]) -> int:
        """Remove workflow run directory."""

        try:
            self.verify_case_path_exists(case_id=case_id)
        except FileNotFoundError:
            self.clean_analyses(case_id)

        if yes or click.confirm(f"Are you sure you want to remove all files in {case_path}?"):
            if case_path.is_symlink():
                LOG.warning(
                    f"Will not automatically delete symlink: {case_path}, delete it manually",
                )
                return EXIT_FAIL

            shutil.rmtree(case_path, ignore_errors=True)
            LOG.info(f"Cleaned {case_path}")
            self.clean_analyses(case_id=case_id)
            return EXIT_SUCCESS

    def _is_flow_cell_check_applicable(self, case_id) -> bool:
        """Returns true if the case is neither down sampled nor external."""
        return not (
            self.status_db.is_case_down_sampled(case_id) or self.status_db.is_case_external(case_id)
        )

    def ensure_flow_cells_on_disk(self, case_id: str) -> None:
        """Check if flow cells are on disk for given case. If not, request flow cells."""
        if not self._is_flow_cell_check_applicable(case_id):
            LOG.info(
                "Flow cell check is not applicable - "
                "the case is either down sampled or external."
            )
            return
        if not self.status_db.are_all_flow_cells_on_disk(case_id=case_id):
            self.status_db.request_flow_cells_for_case(case_id)

    def is_case_ready_for_analysis(self, case_id: str) -> bool:
        if self.get_archive_location_for_case(case_id) == ArchiveLocations.PDC:
            if self._is_flow_cell_check_applicable(
                case_id
            ) and not self.status_db.are_all_flow_cells_on_disk(case_id):
                LOG.warning(f"Case {case_id} is not ready - all flow cells not present on disk.")
                return False
        else:
            if not self.are_all_files_present(case_id):
                LOG.warning(f"Case {case_id} is not ready - some files are archived.")
                return False
        if self.prepare_fastq_api.is_spring_decompression_needed(
            case_id
        ) or self.prepare_fastq_api.is_spring_decompression_running(case_id):
            LOG.warning(f"Case {case_id} is not ready - not all files are decompressed.")
            return False
        return True

    def prepare_fastq_files(self, case_id: str, dry_run: bool) -> None:
        """Retrieves or decompresses fastq files if needed, upon which an AnalysisNotReady error
        is raised."""
        self.ensure_files_are_not_archived(case_id)
        self.resolve_decompression(case_id, dry_run=dry_run)
        if not self.is_case_ready_for_analysis(case_id):
            raise AnalysisNotReadyError("FASTQ file are not present for the analysis to start")

    def ensure_files_are_not_archived(self, case_id: str):
        """Checks if any files are archived and submits a job to retrieve any which are."""
        if self.get_archive_location_for_case(case_id) == ArchiveLocations.PDC:
            self.ensure_flow_cells_on_disk(case_id)
        else:
            if not self.are_all_files_present(case_id):
                spring_archive_api = SpringArchiveAPI(
                    status_db=self.status_db,
                    housekeeper_api=self.housekeeper_api,
                    data_flow_config=self.config.data_flow_config,
                )
                spring_archive_api.retrieve_case(case_id)

    def are_all_files_present(self, case_id: str) -> bool:
        """Returns true if no Spring files are archived in the data location used by the customer tied to the given
        case, and false otherwise."""
        case: Case = self.status_db.get_case_by_internal_id(case_id)
        for sample in [link.sample for link in case.links]:
            if (
                files := self.housekeeper_api.get_archived_files(
                    bundle_name=sample.internal_id, tags=[SequencingFileTag.SPRING]
                )
            ) and not all(file.archive.retrieved_at for file in files):
                return False
        return True

    def get_archive_location_for_case(self, case_id: str) -> str:
        return self.status_db.get_case_by_internal_id(case_id).customer.data_archive_location

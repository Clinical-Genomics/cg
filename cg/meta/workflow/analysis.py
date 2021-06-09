import datetime as dt
import logging
import os
from pathlib import Path
from subprocess import CalledProcessError
from typing import List, Optional, Tuple

from cg.apps.environ import environ_email
from cg.constants import CASE_ACTIONS, Pipeline
from cg.constants.priority import SlurmQos
from cg.exc import BundleAlreadyAddedError, CgDataError, CgError
from cg.meta.meta import MetaAPI
from cg.meta.workflow.fastq import FastqHandler
from cg.models.cg_config import CGConfig
from cg.store import models
from housekeeper.store.models import Bundle, Version

LOG = logging.getLogger(__name__)


class AnalysisAPI(MetaAPI):
    """
    Parent class containing all methods that are either shared or overridden by other workflow APIs.
    """

    def __init__(self, pipeline: Pipeline, config: CGConfig):
        super().__init__(config=config)
        self.pipeline = pipeline
        self._process = None

    @property
    def threshold_reads(self):
        """Defines whether the threshold for adequate read count should be passed for all samples
        when determining if the analysis for a case should be automatically started"""
        return False

    @property
    def process(self):
        raise NotImplementedError

    @property
    def fastq_handler(self):
        return FastqHandler

    def verify_deliverables_file_exists(self, case_id: str) -> None:
        if not Path(self.get_deliverables_file_path(case_id=case_id)).exists():
            raise CgError(f"No deliverables file found for case {case_id}")

    def verify_case_config_file_exists(self, case_id: str):
        if not Path(self.get_case_config_path(case_id=case_id)).exists():
            raise CgError(f"No config file found for case {case_id}")

    def verify_analysis_finish_file_exists(self, case_id: str):
        if not Path(self.get_analysis_finish_path(case_id=case_id)).exists():
            raise CgError(f"No analysis_finish file found for case {case_id}")

    def verify_case_id_in_statusdb(self, case_id: str) -> None:
        """Passes silently if case exists in StatusDB, raises error if case is missing"""

        case_obj: models.Family = self.status_db.family(case_id)
        if not case_obj:
            LOG.error("Case %s could not be found in StatusDB!", case_id)
            raise CgError
        elif not case_obj.links:
            LOG.error("Case %s has no samples in in StatusDB!", case_id)
            raise CgError
        LOG.info("Case %s exists in status db", case_id)

    def check_analysis_ongoing(self, case_id: str) -> None:
        if self.trailblazer_api.is_latest_analysis_ongoing(case_id=case_id):
            LOG.warning(f"{case_id} : analysis is still ongoing - skipping")
            raise CgError(f"Analysis still ongoing in Trailblazer for case {case_id}")

    def verify_case_path_exists(self, case_id: str) -> None:
        if not self.get_case_path(case_id=case_id).exists():
            LOG.error("Working directory path for %s does not exist", case_id)
            raise CgError()

    def all_flowcells_on_disk(self, case_id: str) -> bool:
        """Check if flowcells are on disk for sample before starting the analysis.
        Flowcells not on disk will be requested
        """
        flowcells = self.status_db.flowcells(family=self.status_db.family(case_id))
        statuses = []
        for flowcell_obj in flowcells:
            LOG.info(f"{flowcell_obj.name}: checking if flowcell is on disk")
            LOG.info(f"{flowcell_obj.name}: status is {flowcell_obj.status}")
            statuses.append(flowcell_obj.status or "ondisk")
            if flowcell_obj.status == "removed":
                LOG.info(f"{flowcell_obj.name}: flowcell not on disk, requesting")
                flowcell_obj.status = "requested"
            elif flowcell_obj.status != "ondisk":
                LOG.warning(f"{flowcell_obj.name}: {flowcell_obj.status}")
        self.status_db.commit()
        return all(status == "ondisk" for status in statuses)

    def get_priority_for_case(self, case_id: str) -> str:
        """Fetch priority for case id"""
        case_obj: models.Family = self.status_db.family(case_id)
        if not case_obj.priority or case_obj.priority == 0:
            return SlurmQos.LOW
        if case_obj.priority > 1:
            return SlurmQos.HIGH
        return SlurmQos.NORMAL

    def get_case_path(self, case_id: str) -> Path:
        """Path to case working directory"""
        raise NotImplementedError

    def get_case_config_path(self, case_id) -> Path:
        """Path to case config file"""
        raise NotImplementedError

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        """Path to Trailblazer job id file"""
        raise NotImplementedError

    def get_sample_name_from_lims_id(self, lims_id: str) -> str:
        """Retrieve sample name provided by customer for specific sample"""
        sample_obj: models.Sample = self.status_db.sample(lims_id)
        return sample_obj.name

    def link_fastq_files(self, case_id: str, dry_run: bool = False) -> None:
        """
        Links fastq files from Housekeeper to case working directory
        """
        raise NotImplementedError

    def get_bundle_deliverables_type(self, case_id: str) -> Optional[str]:
        return None

    @staticmethod
    def get_application_type(sample_obj: models.Sample) -> str:
        """
        Gets application type for sample. Only application types supported by trailblazer (or other)
        are valid outputs
        """
        analysis_type: str = sample_obj.application_version.application.prep_category
        if analysis_type and analysis_type.lower() in [
            "wgs",
            "wes",
            "tgs",
        ]:
            return analysis_type.lower()
        return "other"

    def upload_bundle_housekeeper(self, case_id: str) -> None:
        """Storing bundle data in Housekeeper for CASE_ID"""

        LOG.info(f"Storing bundle data in Housekeeper for {case_id}")
        bundle_result: Tuple[Bundle, Version] = self.housekeeper_api.add_bundle(
            bundle_data=self.get_hermes_transformed_deliverables(case_id)
        )
        if not bundle_result:
            raise BundleAlreadyAddedError("Bundle already added to Housekeeper!")
        bundle_object, bundle_version = bundle_result
        self.housekeeper_api.include(bundle_version)
        self.housekeeper_api.add_commit(bundle_object, bundle_version)
        LOG.info(
            f"Analysis successfully stored in Housekeeper: {case_id} : {bundle_version.created_at}"
        )

    def upload_bundle_statusdb(self, case_id: str) -> None:
        """Storing analysis bundle in StatusDB for CASE_ID"""

        LOG.info(f"Storing analysis in StatusDB for {case_id}")
        case_obj: models.Family = self.status_db.family(case_id)
        analysis_start: dt.datetime = self.get_bundle_created_date(case_id=case_id)
        pipeline_version: str = self.get_pipeline_version(case_id=case_id)
        new_analysis: models.Family = self.status_db.add_analysis(
            pipeline=self.pipeline,
            version=pipeline_version,
            started_at=analysis_start,
            completed_at=dt.datetime.now(),
            primary=(len(case_obj.analyses) == 0),
        )
        new_analysis.family = case_obj
        self.status_db.add_commit(new_analysis)
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
            analysis_type=self.get_application_type(self.status_db.family(case_id).links[0].sample),
            out_dir=self.get_trailblazer_config_path(case_id=case_id).parent.as_posix(),
            config_path=self.get_trailblazer_config_path(case_id=case_id).as_posix(),
            priority=self.get_priority_for_case(case_id=case_id),
            data_analysis=str(self.pipeline),
        )

    def get_hermes_transformed_deliverables(self, case_id: str) -> dict:
        return self.hermes_api.create_housekeeper_bundle(
            bundle_name=case_id,
            deliverables=self.get_deliverables_file_path(case_id=case_id),
            pipeline=str(self.pipeline),
            analysis_type=self.get_bundle_deliverables_type(case_id),
            created=self.get_bundle_created_date(case_id),
        ).dict()

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

    def set_statusdb_action(self, case_id: str, action: Optional[str]) -> None:
        """
        Set one of the allowed actions on a case in StatusDB.
        """
        if action in [None, *CASE_ACTIONS]:
            case_obj: models.Family = self.status_db.family(case_id)
            case_obj.action = action
            self.status_db.commit()
            LOG.info("Action %s set for case %s", action, case_id)
            return
        LOG.warning(
            f"Action '{action}' not permitted by StatusDB and will not be set for case {case_id}"
        )

    def get_analyses_to_clean(self, before: dt.datetime) -> List[models.Analysis]:
        analyses_to_clean = self.status_db.analyses_to_clean(pipeline=self.pipeline, before=before)
        return analyses_to_clean.all()

    def get_cases_to_analyze(self) -> List[models.Family]:
        return self.status_db.cases_to_analyze(
            pipeline=self.pipeline, threshold=self.threshold_reads
        )

    def get_running_cases(self) -> List[models.Family]:
        return self.status_db.get_running_cases_for_pipeline(pipeline=self.pipeline)

    def get_cases_to_store(self) -> List[models.Family]:
        raise NotImplementedError

    def get_sample_fastq_destination_dir(self, case_obj: models.Family, sample_obj: models.Sample):
        raise NotImplementedError

    def gather_file_metadata_for_sample(self, sample_obj: models.Sample) -> List[dict]:
        return [
            self.fastq_handler.parse_file_data(file_obj.full_path)
            for file_obj in self.housekeeper_api.files(
                bundle=sample_obj.internal_id, tags=["fastq"]
            )
        ]

    def link_fastq_files_for_sample(
        self, case_obj: models.Family, sample_obj: models.Sample, concatenate: bool = False
    ) -> None:
        """
        Link FASTQ files for a sample to working directory.
        If pipeline input requires concatenated fastq, files can also be concatenated
        """
        linked_reads_paths = {1: [], 2: []}
        concatenated_paths = {1: "", 2: ""}
        files: List[dict] = self.gather_file_metadata_for_sample(sample_obj=sample_obj)
        sorted_files = sorted(files, key=lambda k: k["path"])
        fastq_dir = self.get_sample_fastq_destination_dir(case_obj=case_obj, sample_obj=sample_obj)
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
        """Get target bed filename from lims"""
        case_obj: models.Family = self.status_db.family(case_id)
        sample_obj: models.Sample = case_obj.links[0].sample
        if sample_obj.from_sample:
            sample_obj = self.status_db.sample(internal_id=sample_obj.internal_id)
        target_bed_shortname: str = self.lims_api.capture_kit(sample_obj.internal_id)
        if not target_bed_shortname:
            return target_bed_shortname
        bed_version_obj: Optional[models.BedVersion] = self.status_db.bed_version(
            target_bed_shortname
        )
        if not bed_version_obj:
            raise CgDataError("Bed-version %s does not exist" % target_bed_shortname)
        return bed_version_obj.filename

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
        case_obj: models.Family = self.status_db.family(case_id)
        link: models.FamilySample
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

    def resolve_decompression(self, case_id: str, dry_run: bool) -> bool:
        """
        Handles decompression automatically for case.
        Return True if decompression is running
        """
        if self.prepare_fastq_api.is_spring_decompression_needed(case_id):
            self.decompress_case(case_id=case_id, dry_run=dry_run)
            return True

        if self.prepare_fastq_api.is_spring_decompression_running(case_id):
            self.set_statusdb_action(case_id=case_id, action="analyze")
            return True

        LOG.info("Linking fastq files in housekeeper for case %s", case_id)
        self.prepare_fastq_api.check_fastq_links(case_id)

        if self.prepare_fastq_api.is_spring_decompression_needed(case_id):
            return True

        LOG.info("Decompression for case %s not needed", case_id)
        return False

    @staticmethod
    def get_date_from_file_path(file_path: Path) -> dt.datetime.date:
        """
        Get date from deliverables path using date created metadata.
        """
        return dt.datetime.fromtimestamp(int(os.path.getctime(file_path)))

    def get_additional_naming_metadata(self, sample_obj: models.Sample) -> Optional[str]:
        return None

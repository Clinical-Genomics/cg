import logging
from pathlib import Path
from typing import Optional, List
import datetime as dt

from cg.apps.crunchy import CrunchyAPI
from cg.apps.environ import environ_email
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import Pipeline, CASE_ACTIONS
from cg.exc import (
    BundleAlreadyAddedError,
    CgError,
    LimsDataError,
    CgDataError,
    DecompressionNeededError,
)
from cg.meta.compress import CompressAPI
from cg.meta.workflow.fastq import FastqHandler
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.store import Store, models

LOG = logging.getLogger(__name__)


class AnalysisAPI:
    def __init__(
        self,
        pipeline: Pipeline,
        config: Optional[dict],
    ):
        self.pipeline = pipeline
        self.config = config or {}

        self.housekeeper_api = HousekeeperAPI(self.config)
        self.trailblazer_api = TrailblazerAPI(self.config)
        self.status_db = Store(self.config["database"])
        self.lims_api = LimsAPI(self.config)
        self.hermes_api = HermesApi(self.config)
        self.scout_api = ScoutAPI(self.config)
        self.prepare_fastq_api = PrepareFastqAPI(
            store=self.status_db,
            compress_api=CompressAPI(
                hk_api=self.housekeeper_api, crunchy_api=CrunchyAPI(self.config)
            ),
        )

    @property
    def threshold_reads(self):
        return False

    @property
    def process(self):
        raise NotImplementedError

    @property
    def fastq_handler(self):
        return FastqHandler

    def verify_case_id_in_statusdb(self, case_id: str) -> None:
        """
        Passes silently if case exists in StatusDB, raises error if case is missing
        """
        case_obj: models.Family = self.status_db.family(case_id)
        if not case_obj:
            LOG.error("Case %s could not be found in StatusDB!", case_id)
            raise CgError
        elif not case_obj.links:
            LOG.error("Case %s has no samples in StatusDB!", case_id)
            raise CgError

    def check_analysis_ongoing(self, case_id: str) -> None:
        if self.trailblazer_api.is_latest_analysis_ongoing(case_id=case_id):
            LOG.warning(f"{case_id} : analysis is still ongoing - skipping")
            raise CgError("Analysis still ongoing")

    def get_flowcells(self, case_id: str) -> List[models.Flowcell]:
        """Get all flowcells for all samples in a ticket"""
        flowcells = set()
        case_obj: models.Family = self.status_db.family(case_id)
        for familysample in case_obj.links:
            for flowcell in familysample.sample.flowcells:
                flowcells.add(flowcell)
        return list(flowcells)

    def all_flowcells_on_disk(self, case_id: str) -> bool:
        """Check if flowcells are on disk for sample before starting the analysis.
        Flowcells not on disk will be requested
        """
        flowcells = self.get_flowcells(case_id=case_id)
        statuses = []
        for flowcell_obj in flowcells:
            LOG.debug(f"{flowcell_obj.name}: checking if flowcell is on disk")
            statuses.append(flowcell_obj.status)
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
            return "low"
        if case_obj.priority > 1:
            return "high"
        return "normal"

    def get_case_path(self, case_id: str) -> Path:
        raise NotImplementedError

    def get_case_config_path(self, case_id) -> Path:
        raise NotImplementedError

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        raise NotImplementedError

    def get_sample_name_from_lims_id(self, lims_id: str) -> str:
        """
        Retrieve sample name provided by customer for specific sample
        """
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
        analysis_type = sample_obj.application_version.application.prep_category
        if analysis_type and analysis_type.lower() in [
            "wgs",
            "wes",
            "tgs",
        ]:
            return analysis_type.lower()
        return "other"

    def upload_bundle_housekeeper(self, case_id: str) -> None:
        LOG.info(f"Storing bundle data in Housekeeper for {case_id}")
        bundle_result = self.housekeeper_api.add_bundle(
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
        LOG.info(f"Storing Analysis in ClinicalDB for {case_id}")
        case_obj: models.Family = self.status_db.family(case_id)
        analysis_start: dt.datetime = self.get_bundle_created_date(case_id=case_id)
        pipeline_version: str = self.get_pipeline_version(case_id=case_id)
        new_analysis = self.status_db.add_analysis(
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

    def add_pending_trailblazer_analysis(self, case_id) -> None:
        if self.trailblazer_api.is_latest_analysis_ongoing(case_id=case_id):
            LOG.error("Analysis still ongoing in Trailblazer!")
            raise CgError
        self.trailblazer_api.mark_analyses_deleted(case_id=case_id)
        self.trailblazer_api.add_pending_analysis(
            case_id=case_id,
            email=environ_email(),
            type=self.get_application_type(self.status_db.family(case_id).links[0].sample),
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
        raise NotImplementedError

    def get_pipeline_version(self, case_id: str) -> str:
        raise NotImplementedError

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

    def get_analyses_to_clean(self, before: dt.datetime) -> List[models.Family]:
        analyses_to_clean = self.status_db.analyses_to_clean(pipeline=self.pipeline, before=before)
        return analyses_to_clean.all()

    def get_cases_to_analyze(self) -> List[models.Family]:
        return self.status_db.cases_to_analyze(
            pipeline=self.pipeline, threshold=self.threshold_reads
        )

    def get_running_cases(self) -> List[models.Family]:
        return (
            self.status_db.query(models.Family)
            .filter(models.Family.action == "running")
            .filter(models.Family.data_analysis == self.pipeline)
            .all()
        )

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
        """Link FASTQ files for a sample."""
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

    def get_target_bed_from_lims(self, case_id: str) -> str:
        """Get target bed filename from lims"""
        case_obj: models.Family = self.status_db.family(case_id)
        target_bed_shortname = self.lims_api.capture_kit(case_obj.links[0].sample.internal_id)
        if not target_bed_shortname:
            return target_bed_shortname
        bed_version_obj = self.status_db.bed_version(target_bed_shortname)
        if not bed_version_obj:
            raise CgDataError("Bed-version %s does not exist" % target_bed_shortname)
        return bed_version_obj.filename

    def resolve_decompression(self, case_id: str, dry_run: bool) -> None:
        decompression_needed = self.prepare_fastq_api.is_spring_decompression_needed(case_id)

        if decompression_needed:
            LOG.info(
                "The analysis for %s could not start, decompression is needed",
                case_id,
            )
            decompression_possible = self.prepare_fastq_api.can_at_least_one_sample_be_decompressed(
                case_id
            )
            if decompression_possible:
                possible_to_start_decompression = (
                    self.prepare_fastq_api.can_at_least_one_decompression_job_start(
                        case_id, dry_run
                    )
                )
                if possible_to_start_decompression:
                    if not dry_run:
                        self.set_statusdb_action(case_id=case_id, action="analyze")
                    LOG.info(
                        "Decompression started for %s",
                        case_id,
                    )
                else:
                    LOG.warning(
                        "Decompression failed to start for %s",
                        case_id,
                    )
            else:
                LOG.warning(
                    "Decompression can not be started for %s",
                    case_id,
                )
            raise DecompressionNeededError("Workflow interrupted: decompression is not finished")

        if self.prepare_fastq_api.is_spring_decompression_running(case_id):
            raise DecompressionNeededError("Workflow interrupted: decompression is running")

        LOG.info("Linking fastq files in housekeeper for case %s", case_id)
        self.prepare_fastq_api.check_fastq_links(case_id)

        if self.prepare_fastq_api.is_spring_decompression_needed(case_id):
            raise DecompressionNeededError("Workflow interrupted: decompression is not finished")

        LOG.info("Decompression for case %s not needed", case_id)

"""Module for Balsamic Analysis API"""

import datetime as dt
import gzip
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from typing_extensions import Literal

from cg.apps.balsamic.api import BalsamicAPI
from cg.apps.balsamic.fastq import FastqHandler
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.housekeeper.models import InputBundle
from cg.apps.lims import LimsAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import CASE_ACTIONS, Pipeline
from cg.exc import BalsamicStartError, BundleAlreadyAddedError
from cg.store import Store, models

LOG = logging.getLogger(__name__)


class BalsamicAnalysisAPI:
    """Handles communication between BALSAMIC processes
    and the rest of CG infrastructure"""

    __BALSAMIC_APPLICATIONS = {"wgs", "wes", "tgs"}
    __BALSAMIC_BED_APPLICATIONS = {"wes", "tgs"}

    def __init__(
        self,
        balsamic_api: BalsamicAPI,
        store: Store,
        housekeeper_api: HousekeeperAPI,
        fastq_handler: FastqHandler,
        lims_api: LimsAPI,
        trailblazer_api: TrailblazerAPI,
        hermes_api: HermesApi,
    ):
        self.balsamic_api = balsamic_api
        self.store = store
        self.housekeeper_api = housekeeper_api
        self.fastq_handler = fastq_handler
        self.lims_api = lims_api
        self.trailblazer_api = trailblazer_api
        self.hermes_api = hermes_api

    def get_case_object(self, case_id: str) -> models.Family:
        """Look up case ID in StoreDB and return result"""
        LOG.debug("Fetching case %s", case_id)
        case_object = self.store.family(case_id)
        if not case_object:
            raise BalsamicStartError(f"{case_id} not found in StatusDB!")
        if not case_object.links:
            raise BalsamicStartError(
                f"{case_id} number of samples is {len(case_object.links)}, analysis will not be started!"
            )
        return case_object

    def set_statusdb_action(self, case_id: str, action: str) -> None:
        if action in [None, *CASE_ACTIONS]:
            case_object = self.get_case_object(case_id=case_id)
            case_object.action = action
            self.store.commit()

    def get_case_path(self, case_id: str) -> str:
        """Returns a path where the Balsamic case for the case_id should be located"""
        return Path(self.balsamic_api.root_dir, case_id).as_posix()

    def get_deliverables_file_path(self, case_id: str, check_exists: bool = False) -> str:
        """Returns a path where the Balsamic deliverables file for the case_id should be located.

        (Optional) Checks if deliverables file exists
        """
        LOG.debug("Fetching deliverables file path for %s", case_id)
        deliverables_file_path = Path(
            self.balsamic_api.root_dir,
            case_id,
            "analysis",
            "delivery_report",
            case_id + ".hk",
        )
        if check_exists and not deliverables_file_path.exists():
            raise BalsamicStartError(
                f"No deliverables file found for {case_id}."
                f" Make sure the deliverables file is generated, and try again!"
            )
        return deliverables_file_path.as_posix()

    def get_config_path(self, case_id: str, check_exists: bool = False) -> str:
        """Generates a path where the Balsamic config for the case_id should be located.

        (Optional) Checks if config file exists.
        """
        LOG.debug("Fetch balsamic config file for %s", case_id)
        config_path = Path(self.balsamic_api.root_dir, case_id, case_id + ".json")
        if check_exists and not config_path.exists():
            raise BalsamicStartError(
                f"No config file found for {case_id}. Make sure the config file is generated, and try again!"
            )
        return config_path.as_posix()

    def get_analysis_finish_path(self, case_id: str, check_exists: bool = False) -> str:
        """Returns path to analysis_finish file.
        (Optional) Checks if analysis_finish file exists"""
        analysis_finish_path = Path(
            self.balsamic_api.root_dir, case_id, "analysis", "analysis_finish"
        )
        if check_exists and not analysis_finish_path.exists():
            raise BalsamicStartError(
                f"Analysis incomplete for {case_id}, deliverables file will not be created. "
                f"Please ensure all jobs have finished successfully!"
            )
        return analysis_finish_path.as_posix()

    def get_slurm_job_ids_path(self, case_id: str) -> Path:
        return Path(self.balsamic_api.root_dir, case_id, "analysis", "slurm_jobids.yaml")

    def get_file_collection(self, sample_id: str) -> list:
        """Retrieves sample data for naming"""
        file_objs = self.housekeeper_api.files(bundle=sample_id, tags=["fastq"])
        files = []
        for file_obj in file_objs:
            with gzip.open(file_obj.full_path) as handle:
                header_line = handle.readline().decode()
                header_info = self.fastq_handler.parse_header(header_line)

            data = {
                "path": file_obj.full_path,
                "lane": int(header_info["lane"]),
                "flowcell": header_info["flowcell"],
                "read": int(header_info["readnumber"]),
                "undetermined": ("_Undetermined_" in file_obj.path),
            }
            matches = re.findall(r"-l[1-9]t([1-9]{2})_", file_obj.path)
            if len(matches) > 0:
                data["flowcell"] = f"{data['flowcell']}-{matches[0]}"
            files.append(data)
        return files

    def get_balsamic_sample_objects(self, case_id: str) -> List[models.FamilySample]:
        """Retrieves all links where analysis is set to Balsamic"""
        case_object = self.get_case_object(case_id=case_id)
        return [
            link
            for link in case_object.links
            if str(Pipeline.BALSAMIC) == case_object.data_analysis
        ]

    def get_analysis_type(self, case_id: str) -> str:
        """Return the analysis type for a case

        Analysis types are any of ["tumor_wgs", "tumor_normal_wgs", "tumor_panel", "tumor_normal_panel"]
        """
        LOG.debug("Fetch analysis type for %s", case_id)
        sample_objects: List[models.FamilySample] = self.get_balsamic_sample_objects(
            case_id=case_id
        )
        number_of_samples: int = len(sample_objects)

        application_type: str = self.get_application_type(link_object=sample_objects[0])
        sample_type = "tumor"
        if number_of_samples == 2:
            sample_type = "tumor_normal"
        if application_type != "wgs":
            application_type = "panel"
        analysis_type = "_".join([sample_type, application_type])
        LOG.info("Found analysis type %s", analysis_type)
        return analysis_type

    def link_samples(self, case_id: str) -> None:
        """Links and copies files to working directory"""
        for link_object in self.get_balsamic_sample_objects(case_id=case_id):
            LOG.info(
                f"{link_object.sample.internal_id}: {link_object.family.data_analysis} linking FASTQ files"
            )
            file_collection = self.get_file_collection(sample_id=link_object.sample.internal_id)
            self.fastq_handler.link(
                case=link_object.family.internal_id,
                sample=link_object.sample.internal_id,
                files=file_collection,
            )
        LOG.info("Linking completed")

    def get_target_bed_from_lims(self, link_object: models.FamilySample) -> str:
        """Get target bed filename from lims
        Raises LimsDataError if target_bed cannot be retrieved.
        """
        capture_kit = self.lims_api.capture_kit(link_object.sample.internal_id)
        if capture_kit:
            return self.store.bed_version(capture_kit).filename

    def get_fastq_path(self, link_object: models.FamilySample) -> str:
        """Returns path to the concatenated FASTQ file of a sample"""
        file_collection = self.get_file_collection(sample_id=link_object.sample.internal_id)
        fastq_data = file_collection[0]
        linked_fastq_name = self.fastq_handler.FastqFileNameCreator.create(
            lane=fastq_data["lane"],
            flowcell=fastq_data["flowcell"],
            sample=link_object.sample.internal_id,
            read=fastq_data["read"],
            more={"undetermined": fastq_data["undetermined"]},
        )
        concatenated_fastq_name = self.fastq_handler.FastqFileNameCreator.get_concatenated_name(
            linked_fastq_name
        )
        return Path(
            self.balsamic_api.root_dir,
            link_object.family.internal_id,
            "fastq",
            concatenated_fastq_name,
        ).as_posix()

    @staticmethod
    def get_sample_type(link_object: models.FamilySample) -> str:
        """Returns tissue type of a sample"""
        if link_object.sample.is_tumour:
            return "tumor"
        return "normal"

    @staticmethod
    def get_application_type(link_object: models.FamilySample) -> Literal["wgs", "wes", "tgs"]:
        """Returns application type of a sample."""
        return link_object.sample.application_version.application.prep_category

    def get_priority(self, case_id: str) -> str:
        """Returns priority for the case in clinical-db as text"""
        case_object = self.get_case_object(case_id)
        if case_object.high_priority:
            return "high"
        if case_object.low_priority:
            return "low"
        return "normal"

    def get_verified_bed(self, sample_data: dict, panel_bed: Path) -> Optional[str]:
        """ "Takes a dict with samples and attributes.
        Retrieves unique attributes for application type and target_bed.
        Verifies that those attributes are the same across multiple samples,
        where applicable.
        Verifies that the attributes are valid BALSAMIC attributes
        If application type requires bed, returns path to bed.

        Raises BalsamicStartError:
        - When application type invalid for balsamic
        - When multiple samples have different parameters
        - When bed file required for analysis, but is not set or cannot be retrieved.
        """
        application_types = {v["application_type"].lower() for k, v in sample_data.items()}

        target_beds = {v["target_bed"] for k, v in sample_data.items()}

        if not application_types.issubset(self.__BALSAMIC_APPLICATIONS):
            raise BalsamicStartError("Case application not compatible with BALSAMIC")
        if len(application_types) != 1:
            raise BalsamicStartError("Multiple application types found in LIMS")
        if not application_types.issubset(self.__BALSAMIC_BED_APPLICATIONS):
            if panel_bed:
                raise BalsamicStartError("Cannot set panel_bed for WGS sample!")
            return None
        if panel_bed:
            return panel_bed.as_posix()
        if len(target_beds) == 1:
            target_bed = target_beds.pop()
            if not target_bed:
                raise BalsamicStartError(
                    f"Application type {application_types.pop()} requires a bed file to be analyzed!"
                )
            return Path(self.balsamic_api.bed_path, target_bed).as_posix()
        raise BalsamicStartError(f"Too many BED versions in LIMS: {len(target_beds)}")

    @staticmethod
    def get_verified_tumor_path(sample_data: dict) -> str:
        """Takes a dict with samples and attributes, and returns the path
        of tumor sample.
        If the number of paths is exactly 1, the path is returned.
        Raises BalsamicStartError:
            When there are no tumor samples, or more than one tumor sample
        """
        tumor_paths = [
            val["concatenated_path"]
            for key, val in sample_data.items()
            if val["tissue_type"] == "tumor"
        ]
        if len(tumor_paths) != 1:
            raise BalsamicStartError(
                f"Invalid number of tumor samples: {len(tumor_paths)}, "
                f"BALSAMIC analysis requires exactly 1 tumor sample per case to run successfully!"
            )
        return tumor_paths[0]

    @staticmethod
    def get_verified_normal_path(sample_data: dict) -> Optional[str]:
        """Takes a dict with samples and attributes, and retrieves the path
        of normal sample.
        If the number of paths is exactly 1, the path is returned.
        If there are no paths, then the sample is not paired, and None is returned.
        Raises BalsamicStartError:
            When there is more than one normal sample.
        """
        normal_paths = [
            val["concatenated_path"]
            for key, val in sample_data.items()
            if val["tissue_type"] == "normal"
        ]
        if len(normal_paths) > 1:
            raise BalsamicStartError(
                f"Invalid number of normal samples: {len(normal_paths)}, only up to 1 allowed!!"
            )
        if not normal_paths:
            return None
        return normal_paths[0]

    def get_tumor_sample_name(self, case_id: str) -> Optional[str]:
        sample_obj = (
            self.store.Sample.query.join(models.Family.links, models.FamilySample.sample)
            .filter(models.Family.internal_id == case_id)
            .filter(models.Sample.is_tumour == True)
            .first()
        )
        if sample_obj:
            return sample_obj.internal_id

    def get_normal_sample_name(self, case_id: str) -> Optional[str]:

        sample_obj = (
            self.store.Sample.query.join(models.Family.links, models.FamilySample.sample)
            .filter(models.Family.internal_id == case_id)
            .filter(models.Sample.is_tumour == False)
            .first()
        )
        if sample_obj:
            return sample_obj.internal_id

    def get_verified_config_case_arguments(
        self,
        case_id: str,
        panel_bed: str,
    ) -> dict:
        """Takes a dictionary with per-sample parameters,
        validates them, and transforms into command line arguments
        Raises BalsamicStartError:
            When no samples associated with case are marked for BALSAMIC analysis
        """
        sample_data = self.get_sample_params(case_id=case_id, panel_bed=panel_bed)
        if len(sample_data) == 0:
            raise BalsamicStartError(f"{case_id} has no samples tagged for BALSAMIC analysis!")
        if panel_bed:
            if Path(f"{panel_bed}").is_file():
                panel_bed = Path(f"{panel_bed}")
            else:
                derived_panel_bed = Path(
                    self.balsamic_api.bed_path,
                    self.store.bed_version(panel_bed).filename,
                )
                if not derived_panel_bed.is_file():
                    raise BalsamicStartError(
                        f"{panel_bed} or {derived_panel_bed} are not valid paths to a BED file. "
                        f"Please provide absolute path to desired BED file or a valid bed shortname!"
                    )
                panel_bed = derived_panel_bed

        return {
            "case_id": case_id,
            "normal": self.get_verified_normal_path(sample_data=sample_data),
            "tumor": self.get_verified_tumor_path(sample_data=sample_data),
            "panel_bed": self.get_verified_bed(sample_data=sample_data, panel_bed=panel_bed),
            "tumor_sample_name": self.get_tumor_sample_name(case_id=case_id),
            "normal_sample_name": self.get_normal_sample_name(case_id=case_id),
        }

    @staticmethod
    def print_sample_params(case_id: str, sample_data: dict) -> None:
        """Outputs a table of samples to be displayed in log"""

        LOG.info(f"Case {case_id} has following BALSAMIC samples:")
        LOG.info(
            "{:<20} {:<20} {:<20} {:<20}".format(
                "SAMPLE ID", "TISSUE TYPE", "APPLICATION", "BED VERSION"
            )
        )
        for key in sample_data:
            LOG.info(
                "{:<20} {:<20} {:<20} {:<20}".format(
                    key,
                    str(sample_data[key]["tissue_type"]),
                    str(sample_data[key]["application_type"]),
                    str(sample_data[key]["target_bed"]),
                )
            )
        LOG.info("")

    def get_sample_params(self, case_id: str, panel_bed: Optional[str]) -> dict:

        """Returns a dictionary of attributes for each sample in given family,
        where SAMPLE ID is used as key"""

        sample_data = {
            link_object.sample.internal_id: {
                "tissue_type": self.get_sample_type(link_object),
                "concatenated_path": self.get_fastq_path(link_object),
                "application_type": self.get_application_type(link_object),
                "target_bed": self.resolve_target_bed(panel_bed=panel_bed, link_object=link_object),
            }
            for link_object in self.get_balsamic_sample_objects(case_id=case_id)
        }

        self.print_sample_params(case_id=case_id, sample_data=sample_data)
        return sample_data

    def get_case_application_type(self, case_id: str) -> str:
        application_types = {
            self.get_application_type(link_object)
            for link_object in self.get_balsamic_sample_objects(case_id=case_id)
        }

        if application_types:
            return application_types.pop().lower()

    def resolve_target_bed(
        self, panel_bed: Optional[str], link_object: models.FamilySample
    ) -> Optional[str]:
        if panel_bed:
            return panel_bed
        if self.get_application_type(link_object) not in self.__BALSAMIC_BED_APPLICATIONS:
            return None
        return self.get_target_bed_from_lims(link_object)

    def get_analysis_start(self, case_id: str) -> datetime:
        """Parse the analysis config and return the analysis date"""
        LOG.debug("Fetch analysis start for %s", case_id)
        sample_config = self.get_config_path(case_id=case_id, check_exists=True)
        config_data: dict = json.load(open(sample_config, "r"))
        analysis_start: datetime = datetime.strptime(
            config_data["analysis"]["config_creation_date"], "%Y-%m-%d %H:%M"
        )
        LOG.debug("Found analysis start %s", analysis_start)
        return analysis_start

    def get_pipeline_version(self, case_id: str) -> str:
        LOG.debug("Fetch pipeline version")
        sample_config = self.get_config_path(case_id=case_id, check_exists=True)
        config_data: dict = json.load(open(sample_config, "r"))
        return config_data["analysis"]["BALSAMIC_version"]

    def upload_bundle_housekeeper(self, case_id: str) -> None:
        """ Add analysis bundle to Housekeeper """
        self.get_case_object(case_id=case_id)
        analysis_date: datetime = self.get_analysis_start(case_id=case_id)
        deliverables_file_path: Path = Path(
            self.get_deliverables_file_path(case_id=case_id, check_exists=True)
        )

        hk_bundle: InputBundle = self.hermes_api.create_housekeeper_bundle(
            deliverables=deliverables_file_path,
            pipeline="balsamic",
            analysis_type=self.get_analysis_type(case_id=case_id),
            created=analysis_date,
            bundle_name=case_id,
        )

        bundle_result = self.housekeeper_api.add_bundle(bundle_data=hk_bundle.dict())
        if not bundle_result:
            raise BundleAlreadyAddedError("Bundle already added to Housekeeper!")
        bundle_object, bundle_version = bundle_result
        self.housekeeper_api.include(bundle_version)
        self.housekeeper_api.add_commit(bundle_object, bundle_version)
        LOG.info(
            f"Analysis successfully stored in Housekeeper: {case_id} : {bundle_version.created_at}"
        )

    def upload_analysis_statusdb(self, case_id: str) -> None:
        """ Add Analysis bundle to StatusDB """
        case_object = self.get_case_object(case_id=case_id)
        analysis_start: datetime = self.get_analysis_start(case_id=case_id)
        pipeline_version: str = self.get_pipeline_version(case_id=case_id)
        case_object.action = None
        new_analysis = self.store.add_analysis(
            pipeline=Pipeline.BALSAMIC,
            version=pipeline_version,
            started_at=analysis_start,
            completed_at=dt.datetime.now(),
            primary=(len(case_object.analyses) == 0),
        )
        new_analysis.family = case_object
        self.store.add_commit(new_analysis)
        LOG.info(f"Analysis successfully stored in ClinicalDB: {case_id} : {analysis_start}")

    def family_has_correct_number_tumor_normal_samples(self, case_id: str) -> bool:
        """Evaluates if a case has exactly one tumor and up to one normal sample in ClinicalDB.
        This check is only applied to filter jobs which start automatically"""

        query = (
            self.store.Sample.query.join(models.Family.links, models.FamilySample.sample)
            .filter(models.Family.internal_id == case_id)
            .filter(models.Family.data_analysis == str(Pipeline.BALSAMIC))
        )

        return all(
            [
                len(query.filter(models.Sample.is_tumour == False).all()) <= 1,
                len(query.filter(models.Sample.is_tumour == True).all()) == 1,
            ]
        )

    def get_analyses_to_clean(self, before_date: dt.datetime = dt.datetime.now()) -> list:
        """Retrieve a list of analyses for cleaning created before certain date"""
        analyses_to_clean = self.store.analyses_to_clean(
            pipeline=Pipeline.BALSAMIC, before=before_date
        )
        return analyses_to_clean.all()

    def get_cases_to_analyze(self) -> list:
        """Retrieve a list of balsamic cases without analysis,
        where samples have enough reads to be analyzed"""
        return [
            case_object.internal_id
            for case_object in self.store.cases_to_analyze(
                pipeline=Pipeline.BALSAMIC, threshold=0.75
            )
            if self.family_has_correct_number_tumor_normal_samples(case_object.internal_id)
        ]

    def get_cases_to_store(self) -> list:
        """Retrieve a list of cases where analysis finished successfully,
        and is ready to be stored in Housekeeper"""
        cases_to_store = []
        for case_object in self.store.cases_to_store(pipeline=Pipeline.BALSAMIC):
            case_id = case_object.internal_id
            if Path(self.get_analysis_finish_path(case_id=case_id)).exists():
                cases_to_store.append(case_id)
        return cases_to_store

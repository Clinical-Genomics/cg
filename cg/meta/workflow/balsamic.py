"""Module for Balsamic Analyses"""
import logging
import gzip
import re
import json
import datetime as dt

from pathlib import Path
from typing import Optional

from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.balsamic.api import BalsamicAPI
from cg.apps.balsamic.fastq import FastqHandler
from cg.utils.fastq import FastqAPI
from cg.exc import LimsDataError, BalsamicStartError
from cg.store import Store

LOG = logging.getLogger(__name__)


class BalsamicAnalysisAPI:
    """Handles communication between BALASMIC processes 
    and the rest of CG infrastructure"""

    __BALSAMIC_APPLICATIONS = {"wgs", "wes", "tgs"}
    __BALSAMIC_BED_APPLICATIONS = {"wes", "tgs"}

    def __init__(self, config):
        self.balsamic_api = BalsamicAPI(config)
        self.store = Store(config["database"])
        self.housekeeper_api = HousekeeperAPI(config)
        self.fastq_handler = FastqHandler(config)
        self.lims_api = LimsAPI(config)
        self.fastq_api = FastqAPI

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """Generates a path where the Balsamic deliverables file for the case_id should be
        located"""
        return Path(
            self.balsamic_api.root_dir, case_id, "delivery_report", case_id + ".hk"
        ).as_posix()

    def get_config_path(self, case_id: str) -> Path:
        """Generates a path where the Balsamic config for the case_id should be located"""
        return Path(self.balsamic_api.root_dir, case_id, case_id + ".json").as_posix()

    def get_case_path(self, case_id: str) -> Path:
        """Generates a path where the Balsamic case for the case_id should be located"""
        return Path(self.balsamic_api.root_dir, case_id).as_posix()

    def get_file_collection(self, sample_id: str) -> dict:
        file_objs = self.housekeeper_api.files(bundle=sample_id, tags=["fastq"])
        files = []
        for file_obj in file_objs:
            with gzip.open(file_obj.full_path) as handle:
                header_line = handle.readline().decode()
                header_info = self.fastq_api.parse_header(header_line)

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

    def get_case_object(self, case_id: str):
        """Look up case ID in StoreDB and return result"""
        case_object = self.store.family(case_id)
        return case_object

    def link_samples(self, case_object) -> None:
        """Links and copies files to working directory"""
        for link_object in case_object.links:
            LOG.info(
                "%s: %s link FASTQ files",
                link_object.sample.internal_id,
                link_object.sample.data_analysis,
            )
            if "balsamic" in link_object.sample.data_analysis.lower():
                LOG.info(
                    f"{link_object.sample.internal_id} has balsamic as data analysis, linking."
                )

                file_collection = self.get_file_collection(sample_id=link_object.sample.internal_id)
                self.fastq_handler.link(
                    case=link_object.family.internal_id,
                    sample=link_object.sample.internal_id,
                    files=file_collection,
                )
            else:
                LOG.info(
                    f"{link_object.sample.internal_id} does not have balsamic as data analysis, skipping."
                )
        LOG.info("Linking completed")

    def get_target_bed_from_lims(self, link_object) -> str(Path):
        """Get target bed filename from lims
        Raises LimsDataError if target_bed cannot be retrieved.
        """
        capture_kit = self.lims_api.capture_kit(link_object.sample.internal_id)
        if capture_kit:
            panel_bed = self.store.bed_version(capture_kit).filename
            return panel_bed

    def get_fastq_path(self, link_object) -> str(Path):
        """Returns path to the FASTQ file for a sample"""
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
        concatenated_path = Path(
            self.balsamic_api.root_dir,
            link_object.family.internal_id,
            "fastq",
            concatenated_fastq_name,
        ).as_posix()
        return concatenated_path

    def get_sample_type(self, link_object) -> str:
        """Returns tissue type of a sample"""
        if link_object.sample.is_tumour:
            return "tumor"
        return "normal"

    def get_application_type(self, link_object) -> str:
        """Returns application type of a sample"""
        application_type = link_object.sample.application_version.application.prep_category
        return application_type

    def get_priority(self, case_object) -> str:
        """Finds priority for the case in clinical-db, and returns it as text"""
        if case_object.high_priority:
            return "high"
        if case_object.low_priority:
            return "low"
        return "normal"

    def get_verified_bed(self, sample_data: dict, panel_bed: Path) -> Optional[str]:
        """"Takes a dict with samples and attributes.
        - Retrieves unique attributes for application type and target_bed. 
        - Verifies that those attributes are the same across multiple samples, 
        where applicable.
        - Verifies that the attributes are valid BALSAMIC attributes
        - If application type requires bed, returns path to bed.
        
        Raises BalsamicStartError:
        - When application type invalid for balsamic 
        - When multiple samples have different parameters
        - When bed file required for analysis, but is not set.
        """
        application_types = set([v["application_type"] for k, v in sample_data.items()])
        target_beds = set([v["target_bed"] for k, v in sample_data.items()])

        if not application_types.issubset(self.__BALSAMIC_APPLICATIONS):
            raise BalsamicStartError("Case application not compatible with BALSAMIC")
        if len(application_types) != 1 or len(target_beds) > 1:
            raise BalsamicStartError("Multiple application types or BED versions")
        if not application_types.issubset(self.__BALSAMIC_BED_APPLICATIONS):
            if panel_bed:
                raise BalsamicStartError("Cannot set panel_bed for WGS sample!")
            return None
        if len(target_beds) == 1:
            if panel_bed:
                return Path(self.balsamic_api.bed_path, panel_bed).as_posix()
            return Path(self.balsamic_api.bed_path, target_beds.pop()).as_posix()
        raise BalsamicStartError("No consensus BED version could be retrieved from LIMS")

    def get_verified_tumor_path(self, sample_data: dict) -> str(Path):
        """Takes a dict with samples and attributes, and retrieves the paths
        of tumor samples. 
        If the number of paths is exactly 1, the path is returned.
        If there are no paths, or more than one path, raise BalsamicStartError.
        """
        tumor_paths = [
            val["concatenated_path"]
            for key, val in sample_data.items()
            if val["tissue_type"] == "tumor"
        ]
        if len(tumor_paths) != 1:
            raise BalsamicStartError(f"Invalid number of tumor samples: {len(tumor_paths)}!")
        return tumor_paths[0]

    def get_verified_normal_path(self, sample_data: dict) -> Optional[str]:
        """Takes a dict with samples and attributes, and retrieves the paths
        of normal samples. If the number of paths is exactly 1, the path is returned.
        If there are no paths, then the sample is not paired, and None is returned.
        Otherwise, raise BalsamicStartError.
        """
        normal_paths = [
            val["concatenated_path"]
            for key, val in sample_data.items()
            if val["tissue_type"] == "normal"
        ]
        if len(normal_paths) > 1:
            raise BalsamicStartError(f"Invalid number of normal samples: {len(normal_paths)}!")
        if len(normal_paths) == 0:
            return None
        return normal_paths[0]

    def get_verified_config_params(self, case_id: str, panel_bed: str, sample_data: dict) -> dict:
        """Takes a dictionary with per-sample parameters, 
        verifies their structure, and transforms into command line arguments
        """

        if len(sample_data) == 0:
            raise BalsamicStartError(f"{case_id} has no samples tagged for BALSAMIC analysis!")

        arguments = {
            "case_id": case_id,
            "normal": self.get_verified_normal_path(sample_data=sample_data),
            "tumor": self.get_verified_tumor_path(sample_data=sample_data),
            "panel_bed": self.get_verified_bed(sample_data=sample_data, panel_bed=panel_bed),
        }
        return arguments

    def get_sample_params(self, case_object) -> dict:
        """Fetches attributes for each sample in given family, 
        and returns them as a dictionary where SAMPLE ID is key"""
        sample_data = {}
        for link_object in case_object.links:
            if "balsamic" in link_object.sample.data_analysis.lower():
                sample_data[link_object.sample.internal_id] = {
                    "tissue_type": self.get_sample_type(link_object),
                    "concatenated_path": self.get_fastq_path(link_object),
                    "application_type": self.get_application_type(link_object),
                    "target_bed": self.get_target_bed_from_lims(link_object),
                }
        return sample_data

    def report_sample_table(self, case_id: str, sample_data: dict):
        """Outputs a table of samples to be processed in log"""

        LOG.info(f"Case {case_id} has following BALSAMIC samples:")
        LOG.info(
            "{:<10} {:<10} {:<10} {:<10}".format(
                "SAMPLE ID", "TISSUE TYPE", "APPLICATION", "BED VERSION"
            )
        )
        for key in sample_data:
            LOG.info(
                "{:<10} {:<10} {:<10} {:<10}".format(
                    key,
                    sample_data[key]["tissue_type"],
                    sample_data[key]["application_type"],
                    sample_data[key]["target_bed"],
                )
            )
        LOG.info("")

    def update_housekeeper(self, case_object, sample_config, deliverable_report_path):
        """ WIP
        Store case files in Housekeeper

        name: case_obj.internal_id
        created: dt.datetime.strptime(config["analysis"]["timestamp"], "%Y-%m-%d %H:%M")
        version: config["analysis"]["BALSAMIC_version"]
        files: List[{
            path: Path
            tags: List[]
            archive: Bool = False
        }]

        bundle_obj, bundle_version = hkAPI.add_bundle(bundle_data)
        hkAPI.include(bundle_version)
        hkAPI.add_commit(bundle_obj, bundle_version)

        """

        config_data = dict(json.load(open(sample_config, "r")))
        bundle_data = {
            "name": case_object.internal_id,
            "created": dt.datetime.strptime(
                config_data["analysis"]["config_creation_date"], "%Y-%m-%d %H:%M"
            ),
            "version": config_data["analysis"]["BALSAMIC_version"],
            "files": list(),
        }
        bundle_object, bundle_version = self.housekeeper_api.add_bundle(bundle_data=bundle_data)
        if not bundle_object and bundle_version:
            raise Exception
        self.housekeeper_api.include(bundle_version)
        self.housekeeper_api.add_commit(bundle_object, bundle_version)

    def update_statusdb(self, case_object, sample_config):
        """ WIP
        Update StatusDB

        new_analysis = StoreAPI.add_analysis({
            pipeline="balsamic",
            version=config["BALSAMIC_version"],
            started_at=dt.datetime.strptime(config["analysis"]["timestamp"], "%Y-%m-%d %H:%M"),
            completed_at=dt.datetime.now(),
            primary=(len(case_obj.analyses) == 0)
            })
        new_analysis.family = case_obj

        StoreAPI.add_commit(new_analysis)
        case_obj.actions = None

        """

        config_data = dict(json.load(open(sample_config, "r")))
        new_analysis = self.store.add_analysis(
            {
                "pipeline": "balsamic",
                "version": config_data["analysis"]["BALSAMIC_version"],
                "started_at": dt.datetime.strptime(
                    config_data["analysis"]["config_creation_date"], "%Y-%m-%d %H:%M"
                ),
                "completed_at": dt.datetime.now(),
                "primary": (len(case_object.analyses) == 0),
            }
        )
        new_analysis.family = case_object
        self.store.add_commit(new_analysis)

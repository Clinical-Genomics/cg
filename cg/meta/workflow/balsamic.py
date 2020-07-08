"""Module for Balsamic Analyses"""
import gzip
import re

from typing import Optional
from cg.apps import hk, lims
from cg.apps.balsamic.api import BalsamicAPI
from cg.apps.balsamic.fastq import FastqHandler
from cg.utils.fastq import FastqAPI
from cg.cli.workflow.balsamic.store import store as store_cmd
from cg.cli.workflow.balsamic.deliver import deliver as deliver_cmd
from cg.exc import LimsDataError, BalsamicStartError
from cg.store import Store
from pathlib import Path
import logging

LOG = logging.getLogger(__name__)


class BalsamicAnalysisAPI:
    """Handles communication between BALASMIC processes 
    and the rest of CG infrastructure"""

    __BALSAMIC_APPLICATIONS = {"wgs", "wes", "tgs"}
    __BALSAMIC_BED_APPLICATIONS = {"wes", "tgs"}

    def __init__(self, config):

        self.balsamic_api = BalsamicAPI(config)
        self.store = Store(config["database"])
        self.housekeeper_api = hk.HousekeeperAPI(config)
        self.fastq_handler = FastqHandler(config)
        self.lims_api = lims.LimsAPI(config)
        self.fastq_api = FastqAPI

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """Generates a path where the Balsamic deliverables file for the case_id should be
        located"""
        return Path(self.balsamic_api.root_dir / case_id / "delivery_report" / (case_id + ".hk"))

    def get_config_path(self, case_id: str) -> Path:
        """Generates a path where the Balsamic config for the case_id should be located"""
        return Path(self.balsamic_api.root_dir / case_id / (case_id + ".json")).as_posix()

    def get_case_path(self, case_id: str) -> Path:
        """Generates a path where the Balsamic case for the case_id should be located"""
        return Path(self.balsamic_api.root_dir / case_id).as_posix()

    def get_file_collection(self, sample) -> dict:
        file_objs = self.housekeeper_api.files(bundle=sample, tags=["fastq"])
        files = []

        for file_obj in file_objs:
            # figure out flowcell name from header
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
            # look for tile identifier (HiSeq X runs)
            matches = re.findall(r"-l[1-9]t([1-9]{2})_", file_obj.path)
            if len(matches) > 0:
                data["flowcell"] = f"{data['flowcell']}-{matches[0]}"
            files.append(data)

        return files

    def lookup_samples(self, case_id):
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

                file_collection = self.get_file_collection(sample=link_object.sample.internal_id)
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
        """Get target bed filename from lims"""
        capture_kit = self.lims_api.capture_kit(link_object.sample.internal_id)
        if capture_kit:
            panel_bed = self.store.bed_version(capture_kit).filename
            return panel_bed

    def get_fastq_path(self, link_object) -> str(Path):
        file_collection = self.get_file_collection(sample=link_object.sample.internal_id)
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
            self.balsamic_api.root_dir
            / link_object.family.internal_id
            / "fastq"
            / concatenated_fastq_name
        ).as_posix()
        return concatenated_path

    def get_sample_type(self, link_object) -> str:
        if link_object.sample.is_tumour:
            return "tumor"
        return "normal"

    def get_application_type(self, link_object) -> str:
        application_type = link_object.sample.application_version.application.prep_category
        return application_type

    def get_priority(self, case_object) -> str:
        pass

    def get_case_config_params(self, case_object) -> dict:
        """Fetches config params for each sample and returns them in a dict"""
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

    def get_verified_bed(self, sample_data: dict) -> Optional[str]:
        application_types = set([v["application_type"] for k, v in sample_data.items()])
        target_beds = set([v["target_bed"] for k, v in sample_data.items()])

        if not application_types.issubset(self.__BALSAMIC_APPLICATIONS):
            raise ValueError
        if len(application_types) != 1 or len(target_beds) != 1:
            raise ValueError
        if not application_types.issubset(self.__BALSAMIC_BED_APPLICATIONS):
            return None
        return target_beds.pop()

    def get_verified_tumor_path(self, sample_data: dict) -> str(Path):
        tumor_paths = [
            val["concatenated_path"]
            for key, val in sample_data.items()
            if val["tissue_type"] == "tumor"
        ]
        if len(tumor_paths) != 1:
            raise ValueError
        return tumor_paths[0]

    def get_verified_normal_path(self, sample_data: dict) -> Optional[str]:
        normal_paths = [
            val["concatenated_path"]
            for key, val in sample_data.items()
            if val["tissue_type"] == "normal"
        ]
        if len(normal_paths) > 1:
            raise ValueError
        if len(normal_paths) == 0:
            return None
        return normal_paths[0]

    def get_verified_config_params(self, case_id: str, panel_bed: str, sample_data: dict) -> dict:
        arguments = {
            "case_id": case_id,
            "normal": self.get_verified_normal_path(sample_data),
            "tumor": self.get_verified_tumor_path(sample_data),
            "panel_bed": panel_bed or self.get_verified_bed(sample_data),
            "output_config": f"{case_id}.json",
        }
        return arguments

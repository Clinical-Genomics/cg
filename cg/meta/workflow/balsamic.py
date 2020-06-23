"""Module for Balsamic Analyses"""
import gzip
import re

from cg.apps import hk, lims
from cg.apps.balsamic.api import BalsamicAPI
from cg.apps.balsamic.fastq import FastqHandler
from cg.utils.fastq import FastqAPI
from cg.cli.workflow.balsamic.store import store as store_cmd
from cg.cli.workflow.balsamic.deliver import deliver as deliver_cmd
from cg.cli.workflow.get_links import get_links
from cg.exc import LimsDataError, BalsamicStartError
from cg.meta.workflow.base import get_target_bed_from_lims
from cg.store import Store
from cg.utils.commands import Process
from pathlib import Path
from cg.utils.fastq import FastqAPI
import logging

LOG = logging.getLogger(__name__)

class AnalysisAPI:
    """Methods relevant for Balsamic Analyses"""

    def __init__(self, 
                hk_api: hk.HousekeeperAPI, 
                fastq_api: FastqAPI,
                fastq_handler:FastqHandler):
        self.hk = hk_api
        self.fastq = fastq_api

    @staticmethod
    def get_deliverables_file_path(case_id, root_dir):
        """Generates a path where the Balsamic deliverables file for the case_id should be
        located"""
        return root_dir / case_id / "delivery_report" / (case_id + ".hk")

    @staticmethod
    def get_config_path(root_dir: Path, case_id: str) -> Path:
        """Generates a path where the Balsamic config for the case_id should be located"""
        return root_dir / case_id / (case_id + ".json")

    def link_sample(self, fastq_handler: FastqHandler, sample: str, case: str):
        """Link FASTQ files for a sample."""
        file_objs = self.hk.files(bundle=sample, tags=["fastq"])
        files = []

        for file_obj in file_objs:
            # figure out flowcell name from header
            with gzip.open(file_obj.full_path) as handle:
                header_line = handle.readline().decode()
                header_info = self.fastq.parse_header(header_line)

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

        fastq_handler.link(case=case, sample=sample, files=files)



class MetaBalsamicAPI:
    """Handles communication between BALASMIC processes 
    and the rest of CG infrastructure"""
    def __init__(self, config):

        self.balsamic_api = BalsamicAPI(config)
        self.store = Store(config["database"])
        self.housekeeper_api = hk.HousekeeperAPI(config)
        self.fastq_handler = FastqHandler(config)
        self.lims_api = lims.LimsAPI(config)
        self.fastq_api = FastqAPI

    def get_deliverables_file_path(self, case_id):
        """Generates a path where the Balsamic deliverables file for the case_id should be
        located"""
        return Path(self.balsamic_api.root_dir / case_id / "delivery_report" /
                    (case_id + ".hk"))

    def get_config_path(self, case_id):
        """Generates a path where the Balsamic config for the case_id should be located"""
        return Path(self.balsamic_api.root_dir / case_id / (case_id + ".json"))

    def get_file_collection(self, sample):
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

    def link_samples(self, case_object_links):

        for link_object in case_object_links:
            LOG.info(
                "%s: %s link FASTQ files",
                link_object.sample.internal_id,
                link_object.sample.data_analysis,
            )

            if link_object.sample.data_analysis and "balsamic" in link_object.sample.data_analysis.lower(
            ):
                LOG.info("%s has balsamic as data analysis, linking.",
                         link_object.sample.internal_id)

                file_collection = self.get_file_collection(
                    sample=link_object.sample.internal_id)
                self.fastq_handler.link(case=link_object.family.internal_id,
                                        sample=link_object.sample.internal_id,
                                        files=file_collection)

            else:
                LOG.info(
                    "%s does not have blasamic as data analysis, skipping.",
                    link_object.sample.internal_id)

        LOG.info("Linking completed")

    def get_case_config_params(self, case_id, case_object_links) -> dict:
        """Determines correct config params and returns them in a dict"""

        setup_data = {}
        #Iterate over all links
        for link_object in case_object_links:
            #Check of Balsamic as analysis type
            if link_object.sample.data_analysis and "balsamic" in link_object.sample.data_analysis.lower(
            ):

                #Get file collection for sample id
                file_collection = self.get_file_collection(
                    sample=link_object.sample.internal_id)
                fastq_data = file_collection[0]
                linked_fastq_name = self.fastq_handler.FastqFileNameCreator.create(
                    lane=fastq_data["lane"],
                    flowcell=fastq_data["flowcell"],
                    sample=link_object.sample.internal_id,
                    read=fastq_data["read"],
                    more={"undetermined": fastq_data["undetermined"]})
                concatenated_fastq_name = self.fastq_handler.FastqFileNameCreator.get_concatenated_name(
                    linked_fastq_name)
                concatenated_path = f"{self.balsamic_api.root_dir}/{case_id}/{concatenated_fastq_name}"

                #Block to get application type
                application_type = link_object.sample.application_version.application.prep_category

                #Block to get panel BED
                target_bed_filename = get_target_bed_from_lims(
                    lims=self.lims_api,
                    status_db=self.store,
                    target_bed=link_object.sample.internal_id)

                #Check if tumor
                if link_object.sample.is_tumour:
                    tissue_type = "tumor"
                else:
                    tissue_type = "normal"
                setup_data[link_object.sample.internal_id] = {
                    "tissue_type": tissue_type,
                    "concatenated_path": concatenated_path,
                    "application_type": application_type,
                    "target_bed": target_bed_filename,
                }

        return setup_data
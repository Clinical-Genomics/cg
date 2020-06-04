"""Module for Balsamic Analyses"""
import gzip
import re
from pathlib import Path

from cg.utils.fastq import FastqAPI
from cg.apps import hk
from cg.apps.pipelines.fastqhandler import BaseFastqHandler
from cg.store import Store


class AnalysisAPI:
    """Methods relevant for Balsamic Analyses"""

    def __init__(self, db: Store, hk_api: hk.HousekeeperAPI, fastq_api: FastqAPI):
        self.db = db
        self.hk = hk_api
        self.fastq = fastq_api

    @staticmethod
    def get_deliverables_file_path(case_id, root_dir):
        """Generates a path where the Balsamic deliverables file for the case_id should be
        located"""
        return Path.joinpath(root_dir, case_id, "delivery_report", case_id + ".hk")

    @staticmethod
    def get_config_path(root_dir: Path, case_id: str) -> Path:
        """Generates a path where the Balsamic config for the case_id should be located"""
        return Path.joinpath(root_dir, case_id, case_id + ".json")

    def link_sample(self, fastq_handler: BaseFastqHandler, sample: str, case: str):
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

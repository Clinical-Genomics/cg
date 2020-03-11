"""
    API for compressing files
"""

from pathlib import Path
import os
import logging

from cg.apps import hk, crunchy

LOG = logging.getLogger(__name__)


class CompressAPI:
    def __init__(self, hk_api: hk.HousekeeperAPI, crunchy_api: crunchy.CrunchyAPI):

        self.hk_api = hk_api
        self.crunchy_api = crunchy_api

    @staticmethod
    def get_inode(file_link: Path):
        return os.stat(file_link).st_ino

    @staticmetod
    def get_nlinks(file_link: Path):
        return os.stat(file_link).st_nlink

    def get_fastq_files(self, bundle: str):
        """Fetch all fastq-files for a bundle, and organize them into dictionary

        Returns:
            fastq_dict(dict)
        """
        fastq_files = self.hk_api.get_files(bundle=bundle, tags=["fastq"])
        fastq_dict = {}
        for fastq_file in fastq_files:
            sample_name = Path(fastq_file.full_path).name.split("_")[0]
            if sample_name not in fastq_dict.keys():
                fastq_dict[sample_name] = {
                    "fastq_first_path": None,
                    "fastq_second_path": None,
                }
            if fastq_file.full_path.endswith(FASTQ_FIRST_SUFFIX):
                fastq_dict[sample_name]["fastq_first_path"] = fastq_file.full_path
            if fastq_file.full_path.endswith(FASTQ_SECOND_SUFFIX):
                fastq_dict[sample_name]["fastq_second_path"] = fastq_file.full_path
        return fastq_dict

    def get_bam_files(self, bundle: str):
        """Fetch all bam-files for a bundle, and organize them into dictionary

        Returns:
            fastq_dict(dict)
        """
        bam_files = self.hk_api.get_files(bundle=bundle, tags=["bam"])
        bam_dict = {}
        for bam_file in bam_files:
            sample_name = Path(bam_file.full_path).name.split("_")[0]
            bam_dict[sample_name] = bam_file.full_path
        return bam_dict

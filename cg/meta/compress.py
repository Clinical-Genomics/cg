"""
    API for compressing files
"""

from pathlib import Path
import os
import logging
from copy import deepcopy

from cg.apps import hk, crunchy, scoutapi
from cg.apps.constants import FASTQ_FIRST_SUFFIX, FASTQ_SECOND_SUFFIX

LOG = logging.getLogger(__name__)


class CompressAPI:
    def __init__(
        self,
        hk_api: hk.HousekeeperAPI,
        crunchy_api: crunchy.CrunchyAPI,
        scout_api: scoutapi.ScoutAPI,
    ):

        self.hk_api = hk_api
        self.crunchy_api = crunchy_api
        self.scout_api = scout_api

    @staticmethod
    def get_inode(file_link: Path):
        return os.stat(file_link).st_ino

    @staticmethod
    def get_nlinks(file_link: Path):
        return os.stat(file_link).st_nlink

    def get_bam_files(self, case_id: str):

        scout_case = self.scout_api.get_cases(case_id=case_id)[0]
        last_version = self.hk_api.last_version(bundle=case_id)
        hk_files = self.hk_api.get_files(
            bundle=case_id, tags=["bam", "bai", "bam-index"], version=last_version.id
        )
        hk_files_dict = {Path(file.full_path): file for file in hk_files}
        bam_dict = {}
        for sample in scout_case["individuals"]:
            sample_id = sample["individual_id"]
            bam_path = Path(sample["bam_file"])
            if not bam_path.exists():
                LOG.debug("%s does not exist", bam_path)
                return None
            if self.get_nlinks(bam_path) > 1:
                LOG.debug("%s has more than 1 links to same inode", bam_path)
                return None
            if bam_path not in hk_files_dict.keys():
                LOG.debug("%s not in latest version of housekeeper bundle", bam_path)
                return None
            if bam_path.with_suffix(".bai") not in hk_files_dict.keys():
                LOG.debug("%s has no index-file", bam_path)
                return None
            bam_dict[sample_id] = {
                "bam": hk_files_dict[bam_path],
                "bai": hk_files_dict[bam_path.with_suffix(".bai")],
            }
        return bam_dict

    def compress_case(self, bam_dict: dict, dry_run: bool = False):
        for sample, bam_files in bam_dict.items():
            bam_path = Path(bam_files["bam"].full_path)
            LOG.info("Compressing %s for sample %s", bam_path, sample)
            self.crunchy_api.bam_to_cram(bam_path=bam_path, dry_run=dry_run)

    def scout_case_is_compressed(self, case_id):
        bam_dict = self.get_bam_files(case_id=case_id)
        if not bam_dict:
            return False
        for _, bam_files in bam_dict.items():
            bam_path = Path(bam_files["bam"].full_path)
            if not self.crunchy_api.cram_compression_done(bam_path=bam_path):
                LOG.debug("No cram compression for %s", bam_path)
                return False
        return True

    def update_scout(self, case_id: str, dry_run: bool = False):

        bam_dict = self.get_bam_files(case_id=case_id)
        original_case = self.scout_api.get_cases(case_id=case_id)[0]
        modified_case = deepcopy(original_case)
        for sample_id, bam_files in bam_dict.items():
            bam_path = Path(bam_files["bam"].full_path)
            if self.crunchy_api.cram_compression_done(bam_path=bam_path):
                cram_path = self.crunchy_api.change_suffix_bam_to_cram(
                    bam_path=bam_path
                )
                for scout_sample in modified_case["individuals"]:
                    if scout_sample["individual_id"] == sample_id:
                        LOG.debug("bam_file: %s -> cram_file: %s", bam_path, cram_path)
                        del scout_sample["bam_file"]
                        scout_sample["cram_file"] = cram_path

        if not dry_run:
            LOG.info("updating case in scout...")
            pass

    def update_hk(self, case_id: str, dry_run: bool = False):
        bam_dict = self.get_bam_files(case_id=case_id)
        latest_hk_version = self.hk_api.last_version(bundle=case_id)
        for sample_id, bam_files in bam_dict.items():
            cram_tags = [sample_id, "cram"]
            crai_tags = [sample_id, "cram-index"]
            bam_path = Path(bam_files["bam"].full_path)
            bai_path = Path(bam_files["bai"].full_path)
            cram_path = self.crunchy_api.change_suffix_bam_to_cram(bam_path=bam_path)
            crai_path = cram_path.with_suffix(".crai")
            if self.crunchy_api.cram_compression_done(bam_path=bam_path):
                LOG.debug("%s -> %s, with tags %s", bam_path, cram_path, cram_tags)
                LOG.debug("%s -> %s, with tags %s", bai_path, crai_tags, crai_tags)
                if not dry_run:
                    LOG.info("updating files in housekeeper...")
                    self.hk_api.add_file_with_tags(
                        file=cram_path, version_obj=latest_hk_version, tags=cram_tags
                    )
                    self.hk_api.add_file_with_tags(
                        file=crai_path, version_obj=latest_hk_version, tags=crai_tags
                    )

    def remove_bams(self, case_id: str, dry_run: bool = False):
        bam_files = self.get_bam_files(case_id=case_id)
        for sample_id, bam_files in bam_files.items():
            bam_path = Path(bam_files["bam"].full_path)
            bai_path = Path(bam_files["bai"].full_path)
            flag_path = self.crunchy_api.get_flag_path(file_path=bam_path)
            if self.crunchy_api.cram_compression_done(bam_path=bam_path):
                LOG.debug("Will remove %s, %s, and %s", bam_path, bai_path, flag_path)
                if not dry_run:
                    LOG.info("deleting files...")
                    bam_files["bam"].delete()
                    bam_files["bai"].delete()
                    self.hk_api.commit()
                    bam_path.unlink()
                    bai_path.unlink()
                    flag_path.unlink()

"""
    API for compressing files
"""

from pathlib import Path
import os
import logging
from copy import deepcopy

from cg.apps import hk, crunchy, scoutapi
from cg.constants import FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX

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
    def get_nlinks(file_link: Path):
        return os.stat(file_link).st_nlink

    def get_bam_files(self, case_id: str):

        scout_cases = self.scout_api.get_cases(case_id=case_id)
        if not scout_cases:
            LOG.warning("%s not found in scout", case_id)
            return None
        scout_case = scout_cases[0]
        last_version = self.hk_api.last_version(bundle=case_id)
        if not last_version:
            LOG.warning("No bundle found for %s in housekeeper", case_id)
            return None
        hk_tags = ["bam", "bai", "bam-index"]
        hk_files = []
        for tag in hk_tags:
            hk_files.extend(
                self.hk_api.get_files(
                    bundle=case_id, tags=[tag], version=last_version.id
                )
            )
        if not hk_files:
            LOG.warning("No files found in latest housekeeper version for %s", case_id)
            return None
        hk_files_dict = {Path(file.full_path): file for file in hk_files}
        bam_dict = {}
        for sample in scout_case["individuals"]:
            sample_id = sample["individual_id"]
            bam_file = sample.get("bam_file")
            if not bam_file:
                LOG.warning("No bam file found for sample %s in scout", sample_id)
                return None
            bam_path = Path(bam_file)
            bai_paths = self.crunchy_api.get_index_path(bam_path)
            bai_single_suffix = bai_paths["single_suffix"]
            bai_double_suffix = bai_paths["double_suffix"]
            if not bam_path.exists():
                LOG.warning("%s does not exist", bam_path)
                return None
            if self.get_nlinks(bam_path) > 1:
                LOG.warning("%s has more than 1 links to same inode", bam_path)
                return None
            if bam_path not in hk_files_dict.keys():
                LOG.warning("%s not in latest version of housekeeper bundle", bam_path)
                return None
            if (bai_single_suffix not in hk_files_dict.keys()) and (
                bai_double_suffix not in hk_files_dict.keys()
            ):
                LOG.warning("%s has no index-file", bam_path)
                return None
            bai_path = bai_single_suffix
            if bai_double_suffix.exists():
                bai_path = bai_double_suffix

            bam_dict[sample_id] = {
                "bam": hk_files_dict[bam_path],
                "bai": hk_files_dict[bai_path],
            }
        return bam_dict

    def compress_case_bams(
        self, bam_dict: dict, ntasks: int, mem: int, dry_run: bool = False
    ):
        for sample, bam_files in bam_dict.items():
            bam_path = Path(bam_files["bam"].full_path)
            LOG.info("Compressing %s for sample %s", bam_path, sample)
            self.crunchy_api.bam_to_cram(
                bam_path=bam_path, ntasks=ntasks, mem=mem, dry_run=dry_run
            )

    def clean_bams(self, case_id: str, dry_run: bool = False):
        """Update databases and remove uncompressed BAM files for case if
        compression is done"""
        bam_dict = self.get_bam_files(case_id=case_id)
        if bam_dict:
            self.update_scout(case_id=case_id, bam_dict=bam_dict, dry_run=dry_run)
            self.update_hk(case_id=case_id, bam_dict=bam_dict, dry_run=dry_run)
            self.remove_bams(bam_dict=bam_dict, dry_run=dry_run)

    def update_scout(self, case_id: str, bam_dict: dict, dry_run: bool = False):
        """Update scout with compressed alignment file if present"""
        for sample_id, bam_files in bam_dict.items():
            bam_path = Path(bam_files["bam"].full_path)
            if self.crunchy_api.is_cram_compression_done(bam_path=bam_path):
                cram_path = self.crunchy_api.get_cram_path_from_bam(bam_path=bam_path)
                LOG.info("Scout update for %s:", sample_id)
                LOG.info("%s -> %s", bam_path, cram_path)
                if not dry_run:
                    LOG.info("updating alignment-file for %s in scout...", sample_id)
                    self.scout_api.update_alignment_file(
                        case_id=case_id, sample_id=sample_id, alignment_path=cram_path
                    )

    def update_hk(self, case_id: str, bam_dict: dict, dry_run: bool = False):
        """Update Housekeeper with compressed alignment file if present"""
        latest_hk_version = self.hk_api.last_version(bundle=case_id)
        for sample_id, bam_files in bam_dict.items():
            cram_tags = [sample_id, "cram"]
            crai_tags = [sample_id, "cram-index"]
            bam_path = Path(bam_files["bam"].full_path)
            bai_path = Path(bam_files["bai"].full_path)
            cram_path = self.crunchy_api.get_cram_path_from_bam(bam_path=bam_path)
            crai_path = self.crunchy_api.get_index_path(cram_path)["double_suffix"]
            if self.crunchy_api.is_cram_compression_done(bam_path=bam_path):
                LOG.info("HouseKeeper update for %s:", sample_id)
                LOG.info("%s -> %s, with tags %s", bam_path, cram_path, cram_tags)
                LOG.info("%s -> %s, with tags %s", bai_path, crai_path, crai_tags)
                if not dry_run:
                    LOG.info("updating files in housekeeper...")
                    self.hk_api.add_file(
                        file=cram_path, version_obj=latest_hk_version, tags=cram_tags
                    )
                    self.hk_api.add_file(
                        file=crai_path, version_obj=latest_hk_version, tags=crai_tags
                    )
                    bam_files["bam"].delete()
                    bam_files["bai"].delete()
                    self.hk_api.commit()

    def remove_bams(self, bam_dict: dict, dry_run: bool = False):
        """Remove uncompressed alignment files if compression exists"""
        for sample_id, bam_files in bam_dict.items():
            bam_path = Path(bam_files["bam"].full_path)
            bai_path = Path(bam_files["bai"].full_path)
            flag_path = self.crunchy_api.get_flag_path(file_path=bam_path)
            if self.crunchy_api.is_cram_compression_done(bam_path=bam_path):
                LOG.info("Will remove %s, %s, and %s", bam_path, bai_path, flag_path)
                if not dry_run:
                    LOG.info("deleting files...")
                    bam_path.unlink()
                    bai_path.unlink()
                    flag_path.unlink()

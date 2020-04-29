"""
    API for compressing files
"""

import logging
import os
from pathlib import Path

from cg.apps import crunchy, hk, scoutapi
from cg.constants import (BAM_SUFFIX, FASTQ_FIRST_READ_SUFFIX,
                          FASTQ_SECOND_READ_SUFFIX)

LOG = logging.getLogger(__name__)


class CompressAPI:
    """API for compressing BAM and FASTQ files"""

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
        """Get number of links to path"""
        return os.stat(file_link).st_nlink

    def get_bam_files(self, case_id: str) -> dict:
        """
        Get bam-files that can be compressed for a case

        Returns:
            bam_dict (dict): for each sample in case, give file-object for .bam and .bai files
        """

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
            if bam_path.suffix != BAM_SUFFIX:
                LOG.info("Alignment file does not have suffix %s", BAM_SUFFIX)
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

    def get_fastq_files(self, sample_id: str) -> dict:
        """Get FASTQ files for sample"""
        hk_version = self.hk_api.last_version(bundle=sample_id)
        if not hk_version:
            LOG.warning("No bundle found for sample %s in housekeeper", sample_id)
            return None

        # hk api returns an iterable of file objects
        _hk_files = self.hk_api.get_files(
            bundle=sample_id, tags=["fastq"], version=hk_version.id
        )
        hk_files = [Path(fastq_file.full_path) for fastq_file in _hk_files]
        if len(hk_files) != 2:
            LOG.warning("There has to be a pair of fastq files")
            return None

        fastq_dict = self._sort_fastqs(fastq_files=hk_files)
        if not fastq_dict:
            LOG.info("Could not sort FASTQ files for %s", sample_id)
            return None

        return fastq_dict

    def _sort_fastqs(self, fastq_files: list) -> dict:
        """ Sort list of FASTQ files into correct read pair

        Args:
            fastq_files(list(Path))

        Returns:
            fastq_dict(dict): {"fastq_first_file": Path(file), "fastq_second_file": Path(file)}
        """
        first_fastq_key = "fastq_first_file"
        second_fastq_key = "fastq_second_file"
        fastq_dict = dict()
        for fastq_file in fastq_files:
            if not fastq_file.exists():
                LOG.info("%s does not exist", fastq_file)
                return None
            if self.get_nlinks(file_link=fastq_file) > 1:
                LOG.info("More than 1 inode to same file for %s", fastq_file)
                return None

            if str(fastq_file).endswith(FASTQ_FIRST_READ_SUFFIX):
                fastq_dict[first_fastq_key] = fastq_file
            if str(fastq_file).endswith(FASTQ_SECOND_READ_SUFFIX):
                fastq_dict[second_fastq_key] = fastq_file

        if len(fastq_dict) != 2:
            LOG.warning("Could not find paired fastq files")
            return None

        if not self.check_prefixes(
            fastq_dict[first_fastq_key], fastq_dict[second_fastq_key]
        ):
            LOG.info("FASTQ files does not have matching prefix")
            return None

        return fastq_dict

    @staticmethod
    def check_prefixes(first_fastq: Path, second_fastq: Path) -> bool:
        """Check if two files belong to the same read pair"""
        first_prefix = str(first_fastq.absolute()).replace(FASTQ_FIRST_READ_SUFFIX, "")
        second_prefix = str(second_fastq.absolute()).replace(
            FASTQ_SECOND_READ_SUFFIX, ""
        )
        return first_prefix == second_prefix

    def compress_case_bams(
        self, bam_dict: dict, ntasks: int, mem: int, dry_run: bool = False
    ):
        """Compress bam-files in given dictionary"""
        for sample, bam_files in bam_dict.items():
            bam_path = Path(bam_files["bam"].full_path)
            LOG.info("Compressing %s for sample %s", bam_path, sample)
            self.crunchy_api.bam_to_cram(
                bam_path=bam_path, ntasks=ntasks, mem=mem, dry_run=dry_run
            )

    def compress_case_fastqs(
        self, fastq_dict: dict, ntasks: int, mem: int, dry_run: bool = False
    ):
        """Compress fastq-files in given dictionary"""
        for sample_id, fastq_files in fastq_dict.items():
            fastq_first_path = Path(fastq_files["fastq_first_file"].full_path)
            fastq_second_path = Path(fastq_files["fastq_second_file"].full_path)
            LOG.info(
                "Compressing %s and %s for sample %s into SPRING format",
                fastq_first_path,
                fastq_second_path,
                sample_id,
            )
            self.crunchy_api.fastq_to_spring(
                fastq_first_path=fastq_first_path,
                fastq_second_path=fastq_second_path,
                ntasks=ntasks,
                mem=mem,
                dry_run=dry_run,
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
                        path=cram_path, version_obj=latest_hk_version, tags=cram_tags
                    )
                    self.hk_api.add_file(
                        path=crai_path, version_obj=latest_hk_version, tags=crai_tags
                    )
                    bam_files["bam"].delete()
                    bam_files["bai"].delete()
                    self.hk_api.commit()

    def remove_bams(self, bam_dict: dict, dry_run: bool = False):
        """Remove uncompressed alignment files if compression exists"""
        for _, bam_files in bam_dict.items():
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

    def _is_valid_fastq_suffix(self, fastq_path: Path):
        """ Check that fastq has correct suffix"""
        if str(fastq_path).endswith(FASTQ_FIRST_READ_SUFFIX) or str(
            fastq_path
        ).endswith(FASTQ_SECOND_READ_SUFFIX):
            return True
        return False

"""
    API for compressing files
"""

import logging
import os
from pathlib import Path
from typing import List

from housekeeper.store import models as hk_models

from cg.apps import crunchy, hk, scoutapi
from cg.constants import (BAM_SUFFIX, FASTQ_FIRST_READ_SUFFIX,
                          FASTQ_SECOND_READ_SUFFIX, HK_BAM_TAGS, HK_FASTQ_TAGS)

LOG = logging.getLogger(__name__)


class CompressAPI:
    """API for compressing BAM and FASTQ files"""

    def __init__(
        self,
        hk_api: hk.HousekeeperAPI,
        crunchy_api: crunchy.CrunchyAPI,
        scout_api: scoutapi.ScoutAPI,
        dry_run: bool = False,
    ):

        self.hk_api = hk_api
        self.crunchy_api = crunchy_api
        self.scout_api = scout_api
        self.ntasks = 12
        self.mem = 50
        self.dry_run = dry_run

    def set_dry_run(self, dry_run: bool):
        """Update dry run"""
        self.dry_run = dry_run
        self.crunchy_api.set_dry_run(dry_run)

    # Compression methods
    def compress_case_bam(self, case_id: str) -> bool:
        """Compress the bam files for all individuals of a case"""
        bam_dict = self.get_bam_files(case_id=case_id)
        if not bam_dict:
            return False

        for sample_id in bam_dict:
            bam_files = bam_dict[sample_id]
            bam_path = bam_files["bam_path"].resolve()

            if not self.crunchy_api.is_compression_possible(bam_path):
                LOG.info("BAM to CRAM compression not possible for %s", sample_id)
                return False

            LOG.info("Compressing %s for sample %s", bam_path, sample_id)
            self.crunchy_api.bam_to_cram(bam_path=bam_path, ntasks=self.ntasks, mem=self.mem)

        return True

    def compress_fastq(self, sample_id: str) -> bool:
        """Compress the fastq files for a individual"""
        sample_fastq_dict = self.get_fastq_files(sample_id=sample_id)
        if not sample_fastq_dict:
            LOG.info("Could not find FASTQ files for %s", sample_id)
            return False

        fastq_first = sample_fastq_dict["fastq_first_file"]["path"]
        fastq_second = sample_fastq_dict["fastq_second_file"]["path"]

        if self.crunchy_api.is_compression_possible(fastq_first):
            LOG.warning("FASTQ to SPRING compression already done for %s", sample_id)
            return False

        LOG.info(
            "Compressing %s and %s for sample %s into SPRING format",
            fastq_first,
            fastq_second,
            sample_id,
        )
        self.crunchy_api.fastq_to_spring(
            fastq_first=fastq_first, fastq_second=fastq_second, ntasks=self.ntasks, mem=self.mem,
        )

        return True

    def decompress_spring(self, sample_id: str):
        """Decompress SPRING archive for a sample

        This function will make sure that everything is ready for decompression. If so the spring
        archive will be decompressed into the two fastq files. Housekeeper will be updated to
        include fastq files as well as the spring metadata file will be updated to include date for
        decompression.
        """
        spring_path = self.get_spring_path(sample_id)
        if not self.crunchy_api.is_compression_possible(spring_path):
            LOG.info("SPRING to FASTQ decompression not possible for %s", sample_id)
            return False

        LOG.info(
            "Decompressing %s to FASTQ format for sample %s ", spring_path, sample_id,
        )

        self.crunchy_api.spring_to_fastq(spring_path)
        spring_metadata_path = self.crunchy_api.get_flag_path(spring_path)
        self.crunchy_api.update_metadata_date(spring_metadata_path)

        return True

    # Files methods
    @staticmethod
    def get_nlinks(file_link: Path):
        """Get number of links to path"""
        return os.stat(file_link).st_nlink

    def get_bam_files(self, case_id: str) -> dict:
        """
        Get bam-files that can be compressed for a case

        Returns:
            bam_dict (dict): for each sample in case, give file-object for .bam and .bai files

            {<sample_id>:
                {
                    "bam": hk_models.File,
                    "bam_path": Path,
                    "bai": hk_models.File,
                    "bai_path": Path,
                }
            }
        """

        scout_cases = self.scout_api.get_cases(case_id=case_id)
        if not scout_cases:
            LOG.warning("%s not found in scout", case_id)
            return None
        LOG.debug("Found scout case %s", case_id)

        hk_files_dict = self.get_hk_files_dict(bundle_name=case_id, tags=HK_BAM_TAGS)
        if not hk_files_dict:
            LOG.warning("No files found in latest housekeeper version for %s", case_id)
            return None
        LOG.debug("hk files dict found %s", hk_files_dict)

        hk_file_paths = set(hk_files_dict.keys())

        bam_dict = {}
        for sample in scout_cases[0]["individuals"]:
            sample_id = sample["individual_id"]
            LOG.info("Check bam file for sample %s in scout", sample_id)
            bam_file = sample.get("bam_file")

            bam_path = self.get_bam_path(bam_file, hk_file_paths)
            if not bam_path:
                continue

            bai_path = self.get_bam_index_path(bam_path, hk_file_paths)
            if not bai_path:
                continue

            bam_dict[sample_id] = {
                "bam": hk_files_dict[bam_path],
                "bam_path": bam_path,
                "bai": hk_files_dict[bai_path],
                "bai_path": bai_path,
            }

        return bam_dict

    def get_bam_path(self, bam_file: str, hk_files: List[Path]) -> Path:
        """Take the path to a file in string format and return a path object

        The main purpose of this function is to check if the file is valid.
        """
        if not bam_file:
            LOG.warning("No bam file found")
            return None

        bam_path = Path(bam_file).resolve()
        # Check the bam file
        if bam_path.suffix != BAM_SUFFIX:
            LOG.warning("Alignment file does not have correct suffix %s", BAM_SUFFIX)
            return None

        if not bam_path.exists():
            LOG.warning("%s does not exist", bam_path)
            return None

        if bam_path not in hk_files:
            LOG.warning("%s not in latest version of housekeeper bundle", bam_path)
            return None

        if self.get_nlinks(bam_path) > 1:
            LOG.warning("%s has more than 1 links to same inode", bam_path)
            return None

        return bam_path

    def get_bam_index_path(self, bam_path: Path, hk_files: set) -> Path:
        """Check if a bam has a index file and return it as a path"""

        # Check the index file
        bai_paths = self.crunchy_api.get_index_path(bam_path)
        bai_single_suffix = bai_paths["single_suffix"]
        bai_double_suffix = bai_paths["double_suffix"]

        if (bai_single_suffix not in hk_files) and (bai_double_suffix not in hk_files):
            LOG.warning("%s has no index-file", bam_path)
            return False

        bai_path = bai_single_suffix
        if bai_double_suffix.exists():
            bai_path = bai_double_suffix

        return bai_path

    def get_hk_files_dict(self, bundle_name: str, tags: List[str]) -> dict:
        """Fetch files from latest version in HK
            Return a dict with Path object as keys and hk file objects as values

        Returns:
            {
                Path(file): hk.File(file)
            }

        """
        last_version = self.hk_api.last_version(bundle=bundle_name)
        if not last_version:
            LOG.warning("No bundle found for %s in housekeeper", bundle_name)
            return None
        LOG.debug("Found version obj for %s: %s", bundle_name, repr(last_version))
        hk_files_dict = {}
        tags = set(tags)
        for file_obj in last_version.files:
            file_tags = {tag.name for tag in file_obj.tags}
            if not file_tags.intersection(tags):
                continue
            LOG.debug("Found file %s", file_obj)
            path_obj = Path(file_obj.full_path)
            hk_files_dict[path_obj.resolve()] = file_obj
        return hk_files_dict

    def get_spring_path(self, sample_id: str) -> dict:
        """Get spring path for a sample"""
        hk_files_dict = self.get_hk_files_dict(bundle_name=sample_id, tags=["spring"])
        if hk_files_dict is None:
            return None

        for file_path in hk_files_dict:
            if file_path.suffix == ".spring":
                return file_path
        return None

    def get_fastq_files(self, sample_id: str) -> dict:
        """Get FASTQ files for sample"""
        hk_files_dict = self.get_hk_files_dict(bundle_name=sample_id, tags=HK_FASTQ_TAGS)
        if hk_files_dict is None:
            return None

        sorted_fastqs = self.sort_fastqs(fastq_files=list(hk_files_dict.keys()))
        if not sorted_fastqs:
            LOG.info("Could not sort FASTQ files for %s", sample_id)
            return None
        fastq_dict = {
            "fastq_first_file": {
                "path": sorted_fastqs[0],
                "hk_file": hk_files_dict[sorted_fastqs[0]],
            },
            "fastq_second_file": {
                "path": sorted_fastqs[1],
                "hk_file": hk_files_dict[sorted_fastqs[1]],
            },
        }
        return fastq_dict

    def sort_fastqs(self, fastq_files: list) -> tuple:
        """ Sort list of FASTQ files into correct read pair

        Check that the files exists and are correct

        Args:
            fastq_files(list(Path))

        Returns:
            sorted_fastqs(tuple): (fastq_first, fastq_second)
        """
        first_fastq = second_fastq = None
        for fastq_file in fastq_files:
            if not fastq_file.exists():
                LOG.info("%s does not exist", fastq_file)
                return None

            if self.get_nlinks(file_link=fastq_file) > 1:
                LOG.info("More than 1 inode to same file for %s", fastq_file)
                return None

            if str(fastq_file).endswith(FASTQ_FIRST_READ_SUFFIX):
                first_fastq = fastq_file
            if str(fastq_file).endswith(FASTQ_SECOND_READ_SUFFIX):
                second_fastq = fastq_file

        if not (first_fastq and second_fastq):
            LOG.warning("Could not find paired fastq files")
            return None

        if not self.check_prefixes(first_fastq, second_fastq):
            LOG.info("FASTQ files does not have matching prefix")
            return None

        return (first_fastq, second_fastq)

    @staticmethod
    def check_prefixes(first_fastq: Path, second_fastq: Path) -> bool:
        """Check if two files belong to the same read pair"""
        first_prefix = str(first_fastq.absolute()).replace(FASTQ_FIRST_READ_SUFFIX, "")
        second_prefix = str(second_fastq.absolute()).replace(FASTQ_SECOND_READ_SUFFIX, "")
        return first_prefix == second_prefix

    def clean_bams(self, case_id: str):
        """Update databases and remove uncompressed BAM files for case if compression is done

        Should only clean all files if all bams are compressed for a case
        """
        bam_dict = self.get_bam_files(case_id=case_id)
        if not bam_dict:
            return

        latest_hk_version = self.hk_api.last_version(bundle=case_id)

        for sample_id in bam_dict:
            if not self.crunchy_api.is_cram_compression_done(bam_dict[sample_id]["bam_path"]):
                LOG.info("Cram compression pending for: %s", sample_id)
                LOG.info("Skip cleaning")
                return

        for sample_id in bam_dict:
            bam_files = bam_dict[sample_id]
            bam_path = bam_files["bam_path"]
            bai_path = bam_files["bai_path"]

            hk_bam_file = bam_files["bam"]
            hk_bai_file = bam_files["bai"]
            self.remove_bam(bam_path=bam_path, bai_path=bai_path)
            self.update_scout(case_id=case_id, sample_id=sample_id, bam_path=bam_path)

            self.update_bam_hk(
                sample_id=sample_id,
                hk_bam_file=hk_bam_file,
                hk_bai_file=hk_bai_file,
                hk_version=latest_hk_version,
            )

    def clean_fastq(self, sample_id: str) -> bool:
        """Check that fastq compression is completed for a case and clean

        This means removing compressed fastq files and update housekeeper to point to the new spring
        file and its metadata file
        """
        LOG.info("Clean FASTQ files for %s", sample_id)
        sample_fastq_dict = self.get_fastq_files(sample_id=sample_id)
        if not sample_fastq_dict:
            LOG.info("Could not find FASTQ files for %s", sample_id)
            return False
        fastq_first = sample_fastq_dict["fastq_first_file"]["path"]
        fastq_second = sample_fastq_dict["fastq_second_file"]["path"]

        if not self.crunchy_api.is_spring_compression_done(fastq_first, fastq_second):
            LOG.info("Fastq compression pending for: %s", sample_id)
            return False

        fastq_first_hk = sample_fastq_dict["fastq_first_file"]["hk_file"]
        fastq_second_hk = sample_fastq_dict["fastq_second_file"]["hk_file"]

        self.update_fastq_hk(
            sample_id=sample_id, hk_fastq_first=fastq_first_hk, hk_fastq_second=fastq_second_hk
        )

        self.remove_fastq(fastq_first=fastq_first, fastq_second=fastq_second)
        return True

    # Methods to update scout
    def update_scout(self, case_id: str, sample_id: str, bam_path: Path):
        """Update scout with compressed alignment file if present"""

        cram_path = self.crunchy_api.get_cram_path_from_bam(bam_path=bam_path)
        LOG.info("Updating %s -> %s in Scout", bam_path, cram_path)
        if self.dry_run:
            return
        LOG.info("Updating alignment-file for %s in scout...", sample_id)
        self.scout_api.update_alignment_file(
            case_id=case_id, sample_id=sample_id, alignment_path=cram_path
        )

    # Methods to update housekeeper
    def update_bam_hk(
        self,
        sample_id: str,
        hk_bam_file: hk_models.File,
        hk_bai_file: hk_models.File,
        hk_version: hk_models.Version,
    ):
        """Update Housekeeper with compressed alignment file if present"""
        bam_path = Path(hk_bam_file.full_path)
        bai_path = Path(hk_bai_file.full_path)

        cram_tags = [sample_id, "cram"]
        crai_tags = [sample_id, "cram-index"]
        cram_path = self.crunchy_api.get_cram_path_from_bam(bam_path=bam_path)
        crai_path = self.crunchy_api.get_index_path(cram_path)["double_suffix"]
        LOG.info("HouseKeeper update for %s:", sample_id)
        LOG.info("%s -> %s, with tags %s", bam_path, cram_path, cram_tags)
        LOG.info("%s -> %s, with tags %s", bai_path, crai_path, crai_tags)
        if self.dry_run:
            return

        LOG.info("updating files in housekeeper...")
        self.hk_api.add_file(path=cram_path, version_obj=hk_version, tags=cram_tags)
        self.hk_api.add_file(path=crai_path, version_obj=hk_version, tags=crai_tags)
        hk_bam_file.delete()
        hk_bai_file.delete()
        self.hk_api.commit()

    def update_fastq_hk(
        self, sample_id: str, hk_fastq_first: hk_models.File, hk_fastq_second: hk_models.File,
    ):
        """Update Housekeeper with compressed fastq file"""
        version_obj = self.hk_api.last_version(sample_id)
        fastq_first_path = Path(hk_fastq_first.full_path)
        fastq_second_path = Path(hk_fastq_second.full_path)

        spring_tags = [sample_id, "spring"]
        spring_metadata_tags = [sample_id, "spring-metadata"]
        spring_path = self.crunchy_api.get_spring_path_from_fastq(fastq=fastq_first_path)
        spring_metadata_path = self.crunchy_api.get_flag_path(spring_path)
        LOG.info("Housekeeper update for %s:", sample_id)
        LOG.info(
            "%s, %s -> %s, with tags %s",
            fastq_first_path,
            fastq_second_path,
            spring_path,
            spring_tags,
        )
        LOG.info("Adds %s, with tags %s", spring_metadata_path, spring_metadata_tags)
        if self.dry_run:
            return

        LOG.info("updating files in housekeeper...")
        self.hk_api.add_file(path=spring_path, version_obj=version_obj, tags=spring_tags)
        self.hk_api.add_file(
            path=spring_metadata_path, version_obj=version_obj, tags=spring_metadata_tags
        )
        hk_fastq_first.delete()
        hk_fastq_second.delete()
        self.hk_api.commit()

    # Methods to remove files from disc
    def remove_bam(self, bam_path: Path, bai_path: Path):
        """Remove bam files and flag that cram compression is completed"""
        flag_path = self.crunchy_api.get_flag_path(file_path=bam_path)
        LOG.info("Will remove %s, %s, and %s", bam_path, bai_path, flag_path)
        if self.dry_run:
            return
        bam_path.unlink()
        LOG.info("BAM file %s removed", bam_path)
        bai_path.unlink()
        LOG.info("BAM file index %s removed", bai_path)
        flag_path.unlink()
        LOG.info("Flag file %s removed", flag_path)

    def remove_fastq(self, fastq_first: Path, fastq_second: Path):
        """Remove fastq files"""
        LOG.info("Will remove %s and %s", fastq_first, fastq_second)
        if self.dry_run:
            return
        fastq_first.unlink()
        LOG.debug("First fastq in pair %s removed", fastq_first)
        fastq_second.unlink()
        LOG.debug("Second fastq in pair %s removed", fastq_second)
        LOG.info("Fastq files removed")

    @staticmethod
    def _is_valid_fastq_suffix(fastq_path: Path):
        """ Check that fastq has correct suffix"""
        if str(fastq_path).endswith(FASTQ_FIRST_READ_SUFFIX) or str(fastq_path).endswith(
            FASTQ_SECOND_READ_SUFFIX
        ):
            return True
        return False

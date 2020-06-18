"""
    API for compressing files
"""

import logging
from pathlib import Path

from housekeeper.store import models as hk_models
from sqlalchemy.exc import IntegrityError

from cg.apps import crunchy, hk, scoutapi
from cg.meta.compress import files

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

    def get_latest_version(self, bundle_name: str) -> hk_models.Version:
        """Fetch the latest version of a hk bundle"""
        last_version = self.hk_api.last_version(bundle_name)
        if not last_version:
            LOG.warning("No bundle found for %s in housekeeper", bundle_name)
            return None
        LOG.debug("Found version obj for %s: %s", bundle_name, repr(last_version))
        return last_version

    def get_scout_case(self, case_id: str) -> dict:
        """Fetch a case from scout"""
        scout_cases = self.scout_api.get_cases(case_id=case_id)
        if not scout_cases:
            LOG.warning("%s not found in scout", case_id)
            return None
        LOG.debug("Found scout case %s", case_id)
        return scout_cases[0]

    def get_bam_dict(self, case_id: str, version_obj: hk_models.Version = None) -> dict:
        """Fetch the relevant information and return a dictionary with bam files"""
        version_obj = version_obj or self.get_latest_version(case_id)
        if not version_obj:
            return None

        scout_case = self.get_scout_case(case_id)
        if not scout_case:
            return None

        return files.get_bam_files(case_id=case_id, version_obj=version_obj, scout_case=scout_case)

    # Compression methods
    def compress_case_bam(self, case_id: str) -> bool:
        """Compress the bam files for all individuals of a case"""
        bam_dict = self.get_bam_dict(case_id=case_id)
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

        version_obj = self.get_latest_version(sample_id)
        if not version_obj:
            return False

        sample_fastq_dict = files.get_fastq_files(sample_id=sample_id, version_obj=version_obj)
        if not sample_fastq_dict:
            LOG.info("Could not find FASTQ files for %s", sample_id)
            return False

        fastq_first = sample_fastq_dict["fastq_first_file"]["path"]
        fastq_second = sample_fastq_dict["fastq_second_file"]["path"]

        if not self.crunchy_api.is_compression_possible(fastq_first):
            LOG.warning("FASTQ to SPRING not possible for %s", sample_id)
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
        version_obj = self.get_latest_version(sample_id)
        if not version_obj:
            return False
        spring_path = files.get_spring_path(version_obj)
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

    def case_cram_compression_done(self, bam_files: dict) -> bool:
        """Check if cram compression is done for all individuals of a case"""
        for sample_id in bam_files:
            bam_path = bam_files[sample_id]["bam_path"]
            if not self.crunchy_api.is_cram_compression_done(bam_path):
                LOG.info("Cram compression pending for: %s", sample_id)
                LOG.info("Skip cleaning")
                return False
        return True

    def clean_bams(self, case_id: str) -> bool:
        """Update databases and remove uncompressed BAM files for case if compression is done

        Should only clean all files if all bams are compressed for a case
        """
        version_obj = self.get_latest_version(case_id)
        if not version_obj:
            return False

        bam_files = self.get_bam_dict(case_id=case_id, version_obj=version_obj)
        if not bam_files:
            return False

        if not self.case_cram_compression_done(bam_files):
            return False

        for sample_id in bam_files:
            bam_files_info = bam_files[sample_id]
            bam_path = bam_files_info["bam_path"]
            bai_path = bam_files_info["bai_path"]
            hk_bam_file = bam_files_info["bam"]
            hk_bai_file = bam_files_info["bai"]
            self.remove_bam(bam_path=bam_path, bai_path=bai_path)
            self.update_scout(case_id=case_id, sample_id=sample_id, bam_path=bam_path)

            self.update_bam_hk(
                sample_id=sample_id,
                hk_bam_file=hk_bam_file,
                hk_bai_file=hk_bai_file,
                hk_version=version_obj,
            )
        return True

    def clean_fastq(self, sample_id: str) -> bool:
        """Check that fastq compression is completed for a case and clean

        This means removing compressed fastq files and update housekeeper to point to the new spring
        file and its metadata file
        """
        LOG.info("Clean FASTQ files for %s", sample_id)
        version_obj = self.get_latest_version(sample_id)
        if not version_obj:
            return False

        sample_fastq_dict = files.get_fastq_files(sample_id=sample_id, version_obj=version_obj)
        if not sample_fastq_dict:
            LOG.info("Could not find FASTQ files for %s", sample_id)
            return False

        fastq_first = sample_fastq_dict["fastq_first_file"]["path"]
        fastq_second = sample_fastq_dict["fastq_second_file"]["path"]

        if not self.crunchy_api.is_spring_compression_done(fastq_first):
            LOG.info("Fastq compression pending for: %s", sample_id)
            return False

        fastq_first_hk = sample_fastq_dict["fastq_first_file"]["hk_file"]
        fastq_second_hk = sample_fastq_dict["fastq_second_file"]["hk_file"]

        self.update_fastq_hk(
            sample_id=sample_id, hk_fastq_first=fastq_first_hk, hk_fastq_second=fastq_second_hk
        )

        self.remove_fastq(fastq_first=fastq_first, fastq_second=fastq_second)
        return True

    def add_decompressed_fastq(self, sample_id) -> bool:
        """Adds unpacked fastq files to housekeeper"""
        LOG.info("Adds FASTQ to housekeeper for %s", sample_id)
        version_obj = self.get_latest_version(sample_id)
        if not version_obj:
            return False

        spring_path = files.get_spring_path(version_obj)
        if not self.crunchy_api.is_spring_decompression_done(spring_path):
            LOG.info("SPRING to FASTQ decompression not finished %s", sample_id)
            return False

        for file_obj in version_obj.files:
            if "fastq" in file_obj.tags:
                LOG.warning("Fastq files already exists in housekeeper")
                return False

        LOG.info(
            "Decompressing %s to FASTQ format for sample %s ", spring_path, sample_id,
        )

        spring_metadata_path = self.crunchy_api.get_flag_path(spring_path)
        spring_metadata = self.crunchy_api.get_spring_metadata(spring_metadata_path)
        for file_info in spring_metadata:
            if file_info["file"] == "first_read":
                fastq_first_path = file_info["path"]
            if file_info["file"] == "second_read":
                fastq_second_path = file_info["path"]

        self.add_fastq_hk(
            sample_id=sample_id, fastq_first=fastq_first_path, fastq_second=fastq_second_path
        )

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
        LOG.info("Adding spring file to housekeeper")
        self.hk_api.add_file(path=spring_path, version_obj=version_obj, tags=spring_tags)
        self.hk_api.add_file(
            path=spring_metadata_path, version_obj=version_obj, tags=spring_metadata_tags
        )
        try:
            self.hk_api.commit()
        except IntegrityError:
            LOG.info("Spring file already exists")

        hk_fastq_first.delete()
        hk_fastq_second.delete()
        self.hk_api.commit()

    def add_fastq_hk(self, sample_id: str, fastq_first: Path, fastq_second: Path) -> None:
        """Add fastq files to housekeeper"""
        fastq_tags = [sample_id, "fastq"]
        last_version = self.hk_api.last_version(bundle=sample_id)
        LOG.info(
            "Adds %s, %s to bundle %s with tags %s",
            fastq_first,
            fastq_second,
            sample_id,
            fastq_tags,
        )
        if self.dry_run:
            return

        LOG.info("updating files in housekeeper...")
        self.hk_api.add_file(path=fastq_first, version_obj=last_version, tags=fastq_tags)
        self.hk_api.add_file(path=fastq_second, version_obj=last_version, tags=fastq_tags)
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

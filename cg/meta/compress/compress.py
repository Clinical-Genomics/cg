"""
    API for compressing files
"""

import logging
from pathlib import Path

from housekeeper.store import models as hk_models

from cg.apps import crunchy, hk
from cg.meta.compress import files
from cg.models import CompressionData

LOG = logging.getLogger(__name__)


class CompressAPI:
    """API for compressing BAM and FASTQ files"""

    def __init__(
        self, hk_api: hk.HousekeeperAPI, crunchy_api: crunchy.CrunchyAPI, dry_run: bool = False,
    ):

        self.hk_api = hk_api
        self.crunchy_api = crunchy_api
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

    # Compression methods
    def compress_fastq(self, sample_id: str) -> bool:
        """Compress the fastq files for a individual"""
        LOG.info("Check if FASTQ compression is possible for %s", sample_id)
        version_obj = self.get_latest_version(sample_id)
        if not version_obj:
            return False

        sample_fastq_dict = files.get_fastq_files(sample_id=sample_id, version_obj=version_obj)
        if not sample_fastq_dict:
            return False

        all_ok = True
        for run_name in sample_fastq_dict:
            LOG.info("Check if compression possible for run %s", run_name)
            compression_object = sample_fastq_dict[run_name]["compression_data"]

            if not self.crunchy_api.is_fastq_compression_possible(compression_object):
                LOG.warning("FASTQ to SPRING not possible for %s, run %s", sample_id, run_name)
                all_ok = False
                continue

            LOG.info(
                "Compressing %s and %s for sample %s into SPRING format",
                compression_object.fastq_first,
                compression_object.fastq_second,
                compression_object.sample_id,
            )
            self.crunchy_api.fastq_to_spring(compression_object, sample_id=sample_id)

        return all_ok

    def decompress_spring(self, sample_id: str) -> bool:
        """Decompress SPRING archive for a sample

        This function will make sure that everything is ready for decompression from spring archive
        to fastq files.

            - Housekeeper will be updated to include fastq files
            - Housekeeper will still have the spring and spring metadata file
            - The spring metadata file will be updated to include date for decompression
        """
        version_obj = self.get_latest_version(sample_id)
        if not version_obj:
            return False

        compression_objs = files.get_spring_paths(version_obj)
        for compression_obj in compression_objs:
            if not self.crunchy_api.is_spring_decompression_possible(compression_obj):
                LOG.info("SPRING to FASTQ decompression not possible for %s", sample_id)
                return False

            LOG.info(
                "Decompressing %s to FASTQ format for sample %s ",
                compression_obj.spring_path,
                sample_id,
            )

            self.crunchy_api.spring_to_fastq(compression_obj, sample_id=sample_id)
            self.crunchy_api.update_metadata_date(compression_obj.spring_metadata_path)

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
            return False

        all_cleaned = True
        for run_name in sample_fastq_dict:

            compression_object = sample_fastq_dict[run_name]["compression_data"]

            if not self.crunchy_api.is_fastq_compression_done(compression_object):
                LOG.info("Fastq compression not done for sample %s, run %s", sample_id, run_name)
                all_cleaned = False
                continue

            LOG.info("FASTQ compression done for sample %s, run %s!!", sample_id, run_name)

            fastq_first_hk = sample_fastq_dict[run_name]["fastq_first_file"]["hk_file"]
            fastq_second_hk = sample_fastq_dict[run_name]["fastq_second_file"]["hk_file"]

            self.update_fastq_hk(
                sample_id=sample_id,
                compression_obj=compression_object,
                hk_fastq_first=fastq_first_hk,
                hk_fastq_second=fastq_second_hk,
            )

            self.remove_fastq(
                fastq_first=compression_object.fastq_first,
                fastq_second=compression_object.fastq_second,
            )

        if all_cleaned:
            LOG.info("All FASTQ files cleaned for %s!!", sample_id)

        return all_cleaned

    def add_decompressed_fastq(self, sample_id) -> bool:
        """Adds unpacked fastq files to housekeeper"""
        LOG.info("Adds FASTQ to housekeeper for %s", sample_id)
        version_obj = self.get_latest_version(sample_id)
        if not version_obj:
            return False

        spring_paths = files.get_spring_paths(version_obj)
        for spring_path in spring_paths:
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

    # Methods to update housekeeper
    def update_fastq_hk(
        self,
        sample_id: str,
        compression_obj: CompressionData,
        hk_fastq_first: hk_models.File,
        hk_fastq_second: hk_models.File,
    ):
        """Update Housekeeper with compressed fastq files and spring metadata file"""
        version_obj = self.hk_api.last_version(sample_id)

        spring_tags = [sample_id, "spring"]
        spring_metadata_tags = [sample_id, "spring-metadata"]
        LOG.info("Updating fastq files in housekeeper update for %s:", sample_id)
        LOG.info(
            "%s, %s -> %s, with tags %s",
            compression_obj.fastq_first,
            compression_obj.fastq_second,
            compression_obj.spring_path,
            spring_tags,
        )
        LOG.info(
            "Adds %s, with tags %s", compression_obj.spring_metadata_path, spring_metadata_tags
        )
        if self.dry_run:
            return

        LOG.info("updating files in housekeeper...")
        if files.is_file_in_version(version_obj, compression_obj.spring_path):
            LOG.info("Spring file is already in HK")
        else:
            self.hk_api.add_file(
                path=compression_obj.spring_path, version_obj=version_obj, tags=spring_tags
            )
            self.hk_api.commit()

        if files.is_file_in_version(version_obj, compression_obj.spring_metadata_path):
            LOG.info("Spring metadata file is already in HK")
        else:
            self.hk_api.add_file(
                path=compression_obj.spring_metadata_path,
                version_obj=version_obj,
                tags=spring_metadata_tags,
            )
            self.hk_api.commit()

        LOG.info("Deleting fastq files from housekeeper")
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

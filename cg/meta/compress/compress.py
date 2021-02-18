"""
    API for compressing files. Functionality to compress FASTQ, decompress SPRING and clean files
"""

import logging
from pathlib import Path
from cg.store.queries import get_cases_to_compress
from housekeeper.store import models as housekeeper_models

from cg.apps.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.compress import files
from cg.models import CompressionData, FileData

LOG = logging.getLogger(__name__)


class CompressAPI:
    """API for compressing BAM and FASTQ files"""

    def __init__(self, hk_api: HousekeeperAPI, crunchy_api: CrunchyAPI, dry_run: bool = False):

        self.hk_api = hk_api
        self.crunchy_api = crunchy_api
        self.dry_run = dry_run
        self.get_cases_to_compress = get_cases_to_compress

    def set_dry_run(self, dry_run: bool):
        """Update dry run"""
        self.dry_run = dry_run
        if self.crunchy_api.dry_run is False:
            self.crunchy_api.set_dry_run(dry_run)

    def get_latest_version(self, bundle_name: str) -> housekeeper_models.Version:
        """Fetch the latest version of a hk bundle"""
        last_version = self.hk_api.last_version(bundle_name)
        if not last_version:
            LOG.warning("No bundle found for %s in housekeeper", bundle_name)
            return None
        LOG.debug("Found version obj for %s: %s", bundle_name, repr(last_version))
        return last_version

    # Compression methods
    def compress_fastq(self, sample_id: str) -> bool:
        """Compress the FASTQ files for a individual"""
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
            if FileData.is_empty(compression_object.fastq_first):
                LOG.warning(
                    "Fastq files are empty for %s: %s", sample_id, compression_object.fastq_first
                )
                self.delete_fastq_housekeeper(
                    hk_fastq_first=sample_fastq_dict[run_name]["hk_first"],
                    hk_fastq_second=sample_fastq_dict[run_name]["hk_second"],
                )
                all_ok = False
                continue

            if not self.crunchy_api.is_fastq_compression_possible(compression_object):
                LOG.warning("FASTQ to SPRING not possible for %s, run %s", sample_id, run_name)
                all_ok = False
                continue

            LOG.info(
                "Compressing %s and %s for sample %s into SPRING format",
                compression_object.fastq_first,
                compression_object.fastq_second,
                sample_id,
            )
            self.crunchy_api.fastq_to_spring(compression_object, sample_id=sample_id)

        return all_ok

    def decompress_spring(self, sample_id: str) -> bool:
        """Decompress SPRING archive for a sample

        This function will make sure that everything is ready for decompression from SPRING archive
        to FASTQ files.

            - Housekeeper will be updated to include FASTQ files
            - Housekeeper will still have the SPRING and SPRING metadata file
            - The SPRING metadata file will be updated to include date for decompression
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
        """Check that FASTQ compression is completed for a case and clean

        This means removing compressed FASTQ files and update housekeeper to point to the new SPRING
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
                LOG.info("FASTQ compression not done for sample %s, run %s", sample_id, run_name)
                all_cleaned = False
                continue

            LOG.info("FASTQ compression done for sample %s, run %s!!", sample_id, run_name)

            self.update_fastq_hk(
                sample_id=sample_id,
                compression_obj=compression_object,
                hk_fastq_first=sample_fastq_dict[run_name]["hk_first"],
                hk_fastq_second=sample_fastq_dict[run_name]["hk_second"],
            )

            self.remove_fastq(
                fastq_first=compression_object.fastq_first,
                fastq_second=compression_object.fastq_second,
            )

        if all_cleaned:
            LOG.info("All FASTQ files cleaned for %s!!", sample_id)

        return all_cleaned

    def add_decompressed_fastq(self, sample_id) -> bool:
        """Adds unpacked FASTQ files to housekeeper"""
        LOG.info("Adds FASTQ to Housekeeper for %s", sample_id)
        version_obj = self.get_latest_version(sample_id)
        if not version_obj:
            return False

        spring_paths = files.get_spring_paths(version_obj)
        for compression_object in spring_paths:
            if not self.crunchy_api.is_spring_decompression_done(compression_object):
                LOG.info("SPRING to FASTQ decompression not finished %s", sample_id)
                return False

            fastq_first = compression_object.fastq_first
            fastq_second = compression_object.fastq_second
            if files.is_file_in_version(
                version_obj=version_obj, path=fastq_first
            ) or files.is_file_in_version(version_obj=version_obj, path=fastq_second):
                LOG.warning("FASTQ files already exists in Housekeeper")
                continue

            LOG.info("Adding decompressed FASTQ files to Housekeeper for sample %s ", sample_id)

            self.add_fastq_hk(
                sample_id=sample_id, fastq_first=fastq_first, fastq_second=fastq_second
            )

        return True

    def delete_fastq_housekeeper(
        self, hk_fastq_first: housekeeper_models.File, hk_fastq_second: housekeeper_models.File
    ) -> None:
        """Delete fastq files from housekeeper"""
        LOG.info("Deleting FASTQ files from Housekeeper")
        hk_fastq_first.delete()
        hk_fastq_second.delete()
        self.hk_api.commit()
        LOG.debug("FASTQ files deleted from Housekeeper")

    # Methods to update housekeeper
    def update_fastq_hk(
        self,
        sample_id: str,
        compression_obj: CompressionData,
        hk_fastq_first: housekeeper_models.File,
        hk_fastq_second: housekeeper_models.File,
    ) -> None:
        """Update Housekeeper with compressed FASTQ files and SPRING metadata file"""
        version_obj = self.hk_api.last_version(sample_id)

        spring_tags = [sample_id, "spring"]
        spring_metadata_tags = [sample_id, "spring-metadata"]
        LOG.info("Updating FASTQ files in Housekeeper update for %s:", sample_id)
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

        LOG.info("Updating files in Housekeeper...")
        if files.is_file_in_version(version_obj, compression_obj.spring_path):
            LOG.info("SPRING file is already in Housekeeper")
        else:
            LOG.info("Adding SPRING file to Housekeeper")
            self.hk_api.add_file(
                path=compression_obj.spring_path, version_obj=version_obj, tags=spring_tags
            )
            self.hk_api.commit()

        if files.is_file_in_version(version_obj, compression_obj.spring_metadata_path):
            LOG.info("Spring metadata file is already in Housekeeper")
        else:
            self.hk_api.add_file(
                path=compression_obj.spring_metadata_path,
                version_obj=version_obj,
                tags=spring_metadata_tags,
            )
            self.hk_api.commit()

        self.delete_fastq_housekeeper(hk_fastq_first, hk_fastq_second)

    def add_fastq_hk(self, sample_id: str, fastq_first: Path, fastq_second: Path) -> None:
        """Add FASTQ files to housekeeper"""
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

        LOG.info("Updating files in Housekeeper...")
        self.hk_api.add_file(path=fastq_first, version_obj=last_version, tags=fastq_tags)
        self.hk_api.add_file(path=fastq_second, version_obj=last_version, tags=fastq_tags)
        self.hk_api.commit()

    # Methods to remove files from disc
    def remove_fastq(self, fastq_first: Path, fastq_second: Path):
        """Remove FASTQ files"""
        LOG.info("Will remove %s and %s", fastq_first, fastq_second)
        if self.dry_run:
            return
        fastq_first.unlink()
        LOG.debug("First FASTQ in pair %s removed", fastq_first)
        fastq_second.unlink()
        LOG.debug("Second FASTQ in pair %s removed", fastq_second)
        LOG.info("FASTQ files removed")

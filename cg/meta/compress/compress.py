"""
    API for compressing files. Functionality to compress FASTQ, decompress SPRING and clean files
"""

import logging
import re
from pathlib import Path
from typing import List, Dict

from cg.apps.crunchy import CrunchyAPI
from cg.apps.crunchy.files import update_metadata_date
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.backup.backup import SpringBackupAPI
from cg.meta.compress import files
from cg.models import CompressionData, FileData
from cg.store.models import Sample
from housekeeper.store.models import Version, File

LOG = logging.getLogger(__name__)


class CompressAPI:
    """API for compressing BAM and FASTQ files."""

    def __init__(
        self,
        hk_api: HousekeeperAPI,
        demux_root: str,
        crunchy_api: CrunchyAPI,
        backup_api: SpringBackupAPI = None,
        dry_run: bool = False,
    ):

        self.hk_api: HousekeeperAPI = hk_api
        self.crunchy_api: CrunchyAPI = crunchy_api
        self.backup_api: SpringBackupAPI = backup_api
        self.demux_root: Path = Path(demux_root)
        self.dry_run: bool = dry_run

    def set_dry_run(self, dry_run: bool):
        """Update dry run."""
        self.dry_run = dry_run
        if self.crunchy_api.dry_run is False:
            self.crunchy_api.set_dry_run(dry_run)
        if self.backup_api:
            self.backup_api.dry_run = self.dry_run

    def get_flow_cell_id(self, fastq_path: Path) -> str:
        """Extract the flow cell id from a fastq path assuming flow cell id is the first word in the file name."""
        flow_cell_id: str = ""
        regexp = r"(\A[A-Z0-9]+)"
        try:
            flow_cell_id: str = re.search(regexp, fastq_path.name).group()
        except AttributeError as error:
            LOG.error(error)
            LOG.info(f"Could not find flow cell id from fastq path: {fastq_path.as_posix()}")
        return flow_cell_id

    def compress_fastq(self, sample_id: str) -> bool:
        """Compress the FASTQ files for a individual."""
        LOG.info(f"Check if FASTQ compression is possible for {sample_id}")
        version: Version = self.hk_api.get_latest_bundle_version(bundle_name=sample_id)
        if not version:
            return False

        sample_fastq: Dict[str, dict] = files.get_fastq_files(
            sample_id=sample_id, version_obj=version
        )
        if not sample_fastq:
            return False

        all_ok: bool = True
        for run_name in sample_fastq:
            LOG.info(f"Check if compression possible for run {run_name}")
            compression: CompressionData = sample_fastq[run_name]["compression_data"]
            if FileData.is_empty(compression.fastq_first):
                LOG.warning(f"Fastq files are empty for {sample_id}: {compression.fastq_first}")
                self.delete_fastq_housekeeper(
                    hk_fastq_first=sample_fastq[run_name]["hk_first"],
                    hk_fastq_second=sample_fastq[run_name]["hk_second"],
                )
                all_ok = False
                continue

            if not self.crunchy_api.is_fastq_compression_possible(compression_obj=compression):
                LOG.warning(f"FASTQ to SPRING not possible for {sample_id}, run {run_name}")
                all_ok = False
                continue

            LOG.info(
                f"Compressing {compression.fastq_first} and {compression.fastq_second} for sample {sample_id} into SPRING format"
            )
            self.crunchy_api.fastq_to_spring(compression_obj=compression, sample_id=sample_id)
        return all_ok

    def decompress_spring(self, sample_id: str) -> bool:
        """Decompress SPRING archive for a sample.

        This function will make sure that everything is ready for decompression from SPRING archive
        to FASTQ files.

            - Housekeeper will be updated to include FASTQ files
            - Housekeeper will still have the SPRING and SPRING metadata file
            - The SPRING metadata file will be updated to include date for decompression
            - PDC archived SPRING files will be retrieved and decrypted before decompression
        """
        version: Version = self.hk_api.get_latest_bundle_version(bundle_name=sample_id)
        if not version:
            return False

        compressions: List[CompressionData] = files.get_spring_paths(version_obj=version)
        for compression in compressions:
            if not self.crunchy_api.is_spring_decompression_possible(compression_obj=compression):
                LOG.info(f"SPRING to FASTQ decompression not possible for {sample_id}")
                if not self.backup_api.is_to_be_retrieved_and_decrypted(
                    spring_file_path=compression.spring_path
                ):
                    return False
                LOG.info("Until the SPRING file is retrieved from PDC and decrypted")
                self.backup_api.retrieve_and_decrypt_spring_file(
                    spring_file_path=Path(compression.spring_path)
                )

            LOG.info(
                f"Decompressing {compression.spring_path} to FASTQ format for sample {sample_id}"
            )

            self.crunchy_api.spring_to_fastq(compression_obj=compression, sample_id=sample_id)
            update_metadata_date(spring_metadata_path=compression.spring_metadata_path)
        return True

    def clean_fastq(self, sample_id: str) -> bool:
        """Check that FASTQ compression is completed for a case and clean.

        This means removing compressed FASTQ files and update housekeeper to point to the new SPRING
        file and its metadata file.
        """
        LOG.info(f"Clean FASTQ files for {sample_id}")
        version: Version = self.hk_api.get_latest_bundle_version(bundle_name=sample_id)
        if not version:
            return False

        sample_fastq: Dict[str, dict] = files.get_fastq_files(
            sample_id=sample_id, version_obj=version
        )
        if not sample_fastq:
            return False

        all_cleaned: bool = True
        for run_name in sample_fastq:
            compression: CompressionData = sample_fastq[run_name]["compression_data"]

            if not self.crunchy_api.is_fastq_compression_done(compression_obj=compression):
                LOG.info(f"FASTQ compression not done for sample {sample_id}, run {run_name}")
                all_cleaned = False
                continue

            LOG.info(f"FASTQ compression done for sample {sample_id}, run {run_name}!")

            self.update_fastq_hk(
                sample_id=sample_id,
                compression_obj=compression,
                hk_fastq_first=sample_fastq[run_name]["hk_first"],
                hk_fastq_second=sample_fastq[run_name]["hk_second"],
            )

            self.remove_fastq(
                fastq_first=compression.fastq_first,
                fastq_second=compression.fastq_second,
            )

        if all_cleaned:
            LOG.info(
                f"All FASTQ files cleaned for {sample_id}!",
            )
        return all_cleaned

    def add_decompressed_fastq(self, sample_obj: Sample) -> bool:
        """Adds unpacked FASTQ files to Housekeeper."""
        LOG.info(f"Adds FASTQ to Housekeeper for {sample_obj.internal_id}")
        version: Version = self.hk_api.get_latest_bundle_version(bundle_name=sample_obj.internal_id)
        if not version:
            return False

        spring_paths: List[CompressionData] = files.get_spring_paths(version_obj=version)
        if not spring_paths:
            LOG.warning(f"Could not find any spring paths for {sample_obj.internal_id}")
        for compression in spring_paths:
            if not self.crunchy_api.is_spring_decompression_done(compression):
                LOG.info(f"SPRING to FASTQ decompression not finished {sample_obj.internal_id}")
                return False

            fastq_first: Path = compression.fastq_first
            fastq_second: Path = compression.fastq_second
            if files.is_file_in_version(
                version_obj=version, path=fastq_first
            ) or files.is_file_in_version(version_obj=version, path=fastq_second):
                LOG.warning("FASTQ files already exists in Housekeeper")
                continue

            LOG.info(
                f"Adding decompressed FASTQ files to Housekeeper for sample {sample_obj.internal_id}"
            )

            self.add_fastq_hk(
                sample_obj=sample_obj, fastq_first=fastq_first, fastq_second=fastq_second
            )
        return True

    def delete_fastq_housekeeper(self, hk_fastq_first: File, hk_fastq_second: File) -> None:
        """Delete fastq files from Housekeeper."""
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
        hk_fastq_first: File,
        hk_fastq_second: File,
    ) -> None:
        """Update Housekeeper with compressed FASTQ files and SPRING metadata file."""
        version: Version = self.hk_api.last_version(sample_id)

        spring_tags: List[str] = [sample_id, SequencingFileTag.SPRING]
        spring_metadata_tags: List[str] = [sample_id, SequencingFileTag.SPRING_METADATA]
        LOG.info(f"Updating FASTQ files in Housekeeper update for {sample_id}:")
        LOG.info(
            f"{compression_obj.fastq_first}, {compression_obj.fastq_second} -> {compression_obj.spring_path}, with tags {spring_tags}"
        )
        LOG.info(f"Adds {compression_obj.spring_metadata_path}, with tags {spring_metadata_tags}")
        if self.dry_run:
            return

        LOG.info("Updating files in Housekeeper...")
        if files.is_file_in_version(version_obj=version, path=compression_obj.spring_path):
            LOG.info("SPRING file is already in Housekeeper")
        else:
            LOG.info("Adding SPRING file to Housekeeper")
            self.hk_api.add_file(
                path=compression_obj.spring_path, version_obj=version, tags=spring_tags
            )
            self.hk_api.commit()

        if files.is_file_in_version(version_obj=version, path=compression_obj.spring_metadata_path):
            LOG.info("Spring metadata file is already in Housekeeper")
        else:
            self.hk_api.add_file(
                path=compression_obj.spring_metadata_path,
                version_obj=version,
                tags=spring_metadata_tags,
            )
            self.hk_api.commit()

        self.delete_fastq_housekeeper(
            hk_fastq_first=hk_fastq_first, hk_fastq_second=hk_fastq_second
        )

    def add_fastq_hk(self, sample_obj: Sample, fastq_first: Path, fastq_second: Path) -> None:
        """Add FASTQ files to Housekeeper."""

        if not sample_obj.application_version.application.is_external:
            flow_cell_id: str = self.get_flow_cell_id(fastq_path=fastq_first)
            fastq_tags: List[str] = [flow_cell_id, SequencingFileTag.FASTQ]
        else:
            fastq_tags: List[str] = [sample_obj.internal_id, SequencingFileTag.FASTQ]
        last_version: Version = self.hk_api.last_version(bundle=sample_obj.internal_id)
        LOG.info(
            f"Adds {fastq_first}, {fastq_second} to bundle {sample_obj.internal_id} with tags {fastq_tags}"
        )
        if self.dry_run:
            return

        LOG.info("Updating files in Housekeeper...")
        self.hk_api.add_file(path=fastq_first, version_obj=last_version, tags=fastq_tags)
        self.hk_api.add_file(path=fastq_second, version_obj=last_version, tags=fastq_tags)
        self.hk_api.commit()

    # Methods to remove files from disc
    def remove_fastq(self, fastq_first: Path, fastq_second: Path):
        """Remove FASTQ files."""
        LOG.info(f"Will remove {fastq_first} and {fastq_second}")
        if self.dry_run:
            return
        fastq_first.unlink()
        LOG.debug(f"First FASTQ in pair {fastq_first} removed")
        fastq_second.unlink()
        LOG.debug(f"Second FASTQ in pair {fastq_second} removed")
        LOG.info("FASTQ files removed")

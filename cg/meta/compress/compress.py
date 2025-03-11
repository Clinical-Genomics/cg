"""
    API for compressing files. Functionality to compress FASTQ, decompress SPRING and clean files
"""

import logging
import re
from pathlib import Path

from housekeeper.store.models import File, Version

from cg.apps.crunchy import CrunchyAPI
from cg.apps.crunchy.files import update_metadata_date
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.backup.backup import SpringBackupAPI
from cg.meta.compress import files
from cg.models.compression_data import CompressionData
from cg.store.models import Sample

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
        """Compress the FASTQ files for an individual."""
        LOG.debug(f"Check if FASTQ compression is possible for {sample_id}")
        version: Version = self.hk_api.get_latest_bundle_version(bundle_name=sample_id)
        if not version:
            return False

        sample_fastq: dict[str, dict] = files.get_fastq_files(
            sample_id=sample_id, version_obj=version
        )
        if not sample_fastq:
            return False

        all_ok: bool = True
        for run_name in sample_fastq:
            LOG.info(f"Check if compression possible for run {run_name}")
            compression: CompressionData = sample_fastq[run_name]["compression_data"]
            is_compression_possible: bool = self._is_fastq_compression_possible(
                compression=compression,
                sample_id=sample_id,
            )
            if not is_compression_possible:
                LOG.warning(f"FASTQ to SPRING not possible for {sample_id}, run {run_name}")
                all_ok = False
                continue

            LOG.info(
                f"Compressing {compression.fastq_first} and {compression.fastq_second} for sample {sample_id} into SPRING format"
            )
            self.crunchy_api.fastq_to_spring(compression_obj=compression, sample_id=sample_id)
        return all_ok

    def _is_fastq_compression_possible(self, compression: CompressionData, sample_id: str) -> bool:
        if self._is_spring_archived(compression):
            LOG.debug(f"Found archived Spring file for {sample_id} - compression not possible")
            return False
        return compression.is_fastq_compression_possible

    def _is_spring_archived(self, compression_data: CompressionData) -> bool:
        spring_file: File | None = self.hk_api.get_file_insensitive_path(
            path=compression_data.spring_path
        )
        if (not spring_file) or (not spring_file.archive):
            return False
        return bool(spring_file.archive.archived_at)

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

        compressions: list[CompressionData] = files.get_spring_paths(version_obj=version)
        for compression in compressions:
            if not compression.is_spring_decompression_possible:
                LOG.info(f"SPRING to FASTQ decompression not possible for {sample_id}")
                if compression.is_compression_pending or compression.is_spring_decompression_done:
                    LOG.info(
                        f"Spring file {compression.spring_path.as_posix()} is already being decompressed."
                    )
                    continue
                if not self.backup_api.is_to_be_retrieved_and_decrypted(
                    spring_file_path=compression.spring_path
                ):
                    LOG.warning(f"Could not find {compression.spring_path} on disk")
                    return False
                LOG.info("The SPRING file will be retrieved from PDC and decrypted")
                self.backup_api.retrieve_and_decrypt_spring_file(
                    spring_file_path=Path(compression.spring_path)
                )

            LOG.info(
                f"Decompressing {compression.spring_path} to FASTQ format for sample {sample_id}"
            )

            self.crunchy_api.spring_to_fastq(compression_obj=compression, sample_id=sample_id)
            update_metadata_date(spring_metadata_path=compression.spring_metadata_path)
        return True

    def clean_fastq(self, sample_id: str, archive_location: str) -> bool:
        """Check that FASTQ compression is completed for a case and clean.

        This means removing compressed FASTQ files and update housekeeper to point to the new SPRING
        file and its metadata file.
        """
        LOG.debug(f"Clean FASTQ files for {sample_id}")
        version: Version = self.hk_api.get_latest_bundle_version(bundle_name=sample_id)
        if not version:
            return False

        sample_fastq: dict[str, dict] = files.get_fastq_files(
            sample_id=sample_id, version_obj=version
        )
        if not sample_fastq:
            return False

        all_cleaned: bool = True
        for run_name in sample_fastq:
            compression: CompressionData = sample_fastq[run_name]["compression_data"]
            fastq_first: File = sample_fastq[run_name]["hk_first"]
            fastq_second: File = sample_fastq[run_name]["hk_second"]

            if not self._can_fastqs_be_removed(compression):
                LOG.info(
                    f"FASTQ compression not done for sample {sample_id}, run {run_name}, and spring files are not archived."
                )
                all_cleaned = False
                continue

            LOG.info(f"FASTQs are ready to be removed for sample {sample_id}, run {run_name}!")

            self.update_fastq_hk(
                sample_id=sample_id,
                compression_obj=compression,
                hk_fastq_first=fastq_first,
                hk_fastq_second=fastq_second,
                archive_location=archive_location,
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

    def _can_fastqs_be_removed(self, compression_data: CompressionData) -> bool:
        is_fastq_compression_done: bool = compression_data.is_fastq_compression_done
        spring_file: File | None = self.hk_api.get_file_insensitive_path(
            compression_data.spring_path
        )
        is_spring_archived: bool = (
            spring_file and spring_file.archive and spring_file.archive.archived_at
        )
        return is_fastq_compression_done or is_spring_archived

    def add_decompressed_fastq(self, sample: Sample) -> bool:
        """Adds unpacked FASTQ files to Housekeeper."""
        LOG.info(f"Adds FASTQ to Housekeeper for {sample.internal_id}")
        version: Version = self.hk_api.get_latest_bundle_version(bundle_name=sample.internal_id)
        if not version:
            return False

        spring_paths: list[CompressionData] = files.get_spring_paths(version_obj=version)
        if not spring_paths:
            LOG.warning(f"Could not find any spring paths for {sample.internal_id}")
        for compression in spring_paths:
            if not compression.is_spring_decompression_done:
                LOG.info(f"SPRING to FASTQ decompression not finished {sample.internal_id}")
                return False

            fastq_first: Path = compression.fastq_first
            fastq_second: Path = compression.fastq_second
            if files.is_file_in_version(
                version_obj=version, path=fastq_first
            ) or files.is_file_in_version(version_obj=version, path=fastq_second):
                LOG.warning("FASTQ files already exists in Housekeeper")
                continue

            LOG.info(
                f"Adding decompressed FASTQ files to Housekeeper for sample {sample.internal_id}"
            )
            fastq_tags: list[str] = self.get_fastq_tag_names(compression.spring_path)
            self.add_fastq_hk(
                fastq_first=fastq_first,
                fastq_second=fastq_second,
                sample_internal_id=sample.internal_id,
                fastq_tags=fastq_tags,
            )
        return True

    def delete_fastq_housekeeper(self, hk_fastq_first: File, hk_fastq_second: File) -> None:
        """Delete fastq files from Housekeeper."""
        LOG.info("Deleting FASTQ files from Housekeeper")
        self.hk_api.delete_file(file_id=hk_fastq_first.id)
        self.hk_api.delete_file(file_id=hk_fastq_second.id)
        LOG.debug("FASTQ files deleted from Housekeeper")

    # Methods to update housekeeper
    def update_fastq_hk(
        self,
        sample_id: str,
        compression_obj: CompressionData,
        hk_fastq_first: File,
        hk_fastq_second: File,
        archive_location: str,
    ) -> None:
        """Update Housekeeper with compressed FASTQ files and SPRING metadata file."""
        version: Version = self.hk_api.last_version(sample_id)
        spring_tags: list[str] = self.get_spring_tags_from_fastq(hk_fastq_first)
        spring_tags.append(archive_location)
        spring_metadata_tags: list[str] = self.get_spring_metadata_tags_from_fastq(hk_fastq_first)
        LOG.info(f"Updating FASTQ files in Housekeeper for {sample_id}")
        LOG.info(
            f"{compression_obj.fastq_first}, {compression_obj.fastq_second} -> {compression_obj.spring_path}, "
            f"with tags {spring_tags}"
        )
        LOG.info(f"Adds {compression_obj.spring_metadata_path}, with tags {spring_metadata_tags}")
        if self.dry_run:
            return

        LOG.info("Updating files in Housekeeper...")
        if files.is_file_in_version(version_obj=version, path=compression_obj.spring_path):
            LOG.info("SPRING file is already in Housekeeper")
        else:
            LOG.info("Adding SPRING file to Housekeeper")
            self.hk_api.add_and_include_file_to_latest_version(
                bundle_name=sample_id, file=compression_obj.spring_path, tags=spring_tags
            )
            self.hk_api.commit()

        if files.is_file_in_version(version_obj=version, path=compression_obj.spring_metadata_path):
            LOG.info("SPRING metadata file is already in Housekeeper")
        else:
            LOG.info("Adding SPRING metadata file to Housekeeper")
            self.hk_api.add_and_include_file_to_latest_version(
                bundle_name=sample_id,
                file=compression_obj.spring_metadata_path,
                tags=spring_metadata_tags,
            )
            self.hk_api.commit()

        self.delete_fastq_housekeeper(
            hk_fastq_first=hk_fastq_first, hk_fastq_second=hk_fastq_second
        )

    def get_spring_metadata_tags_from_fastq(self, fastq_file: File) -> list[str]:
        non_fastq_tags: list[str] = self.get_all_non_fastq_tags(fastq_file)
        return non_fastq_tags + [SequencingFileTag.SPRING_METADATA]

    def get_spring_tags_from_fastq(self, fastq_file: File) -> list[str]:
        non_fastq_tags: list[str] = self.get_all_non_fastq_tags(fastq_file)
        return non_fastq_tags + [SequencingFileTag.SPRING]

    @staticmethod
    def get_all_non_fastq_tags(fastq_file: File) -> list[str]:
        """Returns a list with all tags except 'fastq' for the fastq_first file of the given fastq file."""
        fastq_tags: list[str] = [tag.name for tag in fastq_file.tags]
        fastq_tags.remove(SequencingFileTag.FASTQ)
        return fastq_tags

    def add_fastq_hk(
        self,
        sample_internal_id: str,
        fastq_first: Path,
        fastq_second: Path,
        fastq_tags: list[str],
    ) -> None:
        """Add decompressed FASTQ files to Housekeeper."""
        LOG.info(
            f"Adds {fastq_first}, {fastq_second} to bundle {sample_internal_id} with tags {fastq_tags}"
        )
        if self.dry_run:
            return

        LOG.info("Updating files in Housekeeper...")
        for fastq in [fastq_first, fastq_second]:
            self.hk_api.add_and_include_file_to_latest_version(
                bundle_name=sample_internal_id, file=fastq, tags=fastq_tags
            )
        self.hk_api.commit()

    def get_fastq_tag_names(self, spring_path: Path) -> list[str]:
        """Returns a list containing all non-spring tag names of the specified file,
        together with the fastq tag name."""
        spring_file: File = self.hk_api.get_file_insensitive_path(path=spring_path)
        spring_file_tags: list[str] = self.hk_api.get_tag_names_from_file(spring_file)
        spring_file_tags.remove(SequencingFileTag.SPRING)
        return spring_file_tags + [SequencingFileTag.FASTQ]

    # Methods to remove files from disc
    def remove_fastq(self, fastq_first: Path, fastq_second: Path):
        """Remove FASTQ files."""
        LOG.info(f"Will remove {fastq_first} and {fastq_second}")
        if self.dry_run:
            return
        for fastq_file in [fastq_first, fastq_second]:
            if fastq_file.exists():
                fastq_file.unlink()
                LOG.debug(f"FASTQ file {fastq_file} removed")

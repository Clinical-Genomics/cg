"""API to prepare fastq files for analysis"""

import logging
from pathlib import Path

from housekeeper.store.models import File, Version

from cg.apps.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.constants import PIPELINES_USING_PARTIAL_ANALYSES
from cg.meta.compress import files
from cg.meta.compress.compress import CompressAPI
from cg.models import CompressionData
from cg.store.models import Case, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class PrepareFastqAPI:
    def __init__(self, store: Store, compress_api: CompressAPI):
        self.store: Store = store
        self.hk_api: HousekeeperAPI = compress_api.hk_api
        self.compress_api: CompressAPI = compress_api
        self.crunchy_api: CrunchyAPI = compress_api.crunchy_api

    def get_compression_objects(self, case_id: str) -> list[CompressionData]:
        """Return a list of compression objects"""
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        compression_objects = []
        for link in case.links:
            sample: Sample = link.sample
            sample_id = sample.internal_id
            if self._should_skip_sample(case=case, sample=sample):
                LOG.warning(f"Skipping sample {sample_id} - it has no reads.")
                continue
            version_obj: Version = self.compress_api.hk_api.get_latest_bundle_version(
                bundle_name=sample_id
            )
            compression_objects.extend(files.get_spring_paths(version_obj))
        return compression_objects

    def get_sample_compression_objects(self, sample_id: str) -> list[CompressionData]:
        compression_objects: list[CompressionData] = []
        version_obj: Version = self.compress_api.hk_api.get_latest_bundle_version(
            bundle_name=sample_id
        )
        compression_objects.extend(files.get_spring_paths(version_obj))
        return compression_objects

    def is_sample_decompression_needed(self, sample_id: str) -> bool:
        """Check if decompression is needed for the specified sample."""
        LOG.debug(f"Checking if decompression is needed for {sample_id}.")
        compression_objects = self.get_sample_compression_objects(sample_id=sample_id)
        return any(
            not self.crunchy_api.is_compression_pending(compression_object)
            and not compression_object.pair_exists()
            for compression_object in compression_objects
        )

    @staticmethod
    def _should_skip_sample(case: Case, sample: Sample):
        """
        For some workflows, we want to start a partial analysis disregarding the samples with no reads.
        This method returns true if we should skip the sample.
        """
        if case.data_analysis in PIPELINES_USING_PARTIAL_ANALYSES and not sample.has_reads:
            return True
        return False

    def is_spring_decompression_needed(self, case_id: str) -> bool:
        """Check if spring decompression needs to be started"""
        compression_objects = self.get_compression_objects(case_id=case_id)
        return any(
            not self.crunchy_api.is_compression_pending(compression_object)
            and not compression_object.pair_exists()
            for compression_object in compression_objects
        )

    def is_spring_decompression_running(self, case_id: str) -> bool:
        """Check if case is being decompressed"""
        compression_objects = self.get_compression_objects(case_id=case_id)
        return any(
            self.crunchy_api.is_compression_pending(compression_object)
            for compression_object in compression_objects
        )

    def can_at_least_one_sample_be_decompressed(self, case_id: str) -> bool:
        """Returns True if at least one sample can be decompressed, otherwise False"""
        compression_objects: list[CompressionData] = self.get_compression_objects(case_id=case_id)
        return any(
            self.crunchy_api.is_spring_decompression_possible(compression_object)
            for compression_object in compression_objects
        )

    def add_decompressed_fastq_files_to_housekeeper(self, case_id: str) -> None:
        """Adds decompressed FASTQ files to Housekeeper for a case, if there are any."""
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        for sample in case.samples:
            self.add_decompressed_sample(sample=sample, case=case)

    def add_decompressed_sample(self, sample: Sample, case: Case) -> None:
        """Adds decompressed FASTQ files to Housekeeper for a sample, if there are any."""
        sample_id = sample.internal_id
        if self._should_skip_sample(case=case, sample=sample):
            LOG.warning(f"Skipping sample {sample_id} - it has no reads.")
            return
        version: Version = self.compress_api.hk_api.get_latest_bundle_version(bundle_name=sample_id)
        fastq_files: dict[Path, File] = files.get_hk_files_dict(
            tags=[SequencingFileTag.FASTQ], version_obj=version
        )
        compressions: list[CompressionData] = files.get_spring_paths(version)
        for compression in compressions:
            self.add_decompressed_spring_object(
                compression=compression, fastq_files=fastq_files, sample=sample
            )

    def add_decompressed_spring_object(
        self, compression: CompressionData, fastq_files: dict[Path, File], sample: Case
    ) -> None:
        """Adds decompressed FASTQ files to Housekeeper related to a single spring file."""
        result = True
        sample_id: str = sample.internal_id
        if not self.are_fastqs_in_housekeeper(compression=compression, fastq_files=fastq_files):
            LOG.info(f"Adding FASTQ files to sample {sample_id} in Housekeeper")
            result: bool = self.compress_api.add_decompressed_fastq(sample)
        else:
            LOG.info(
                f"Both {compression.fastq_first} and {compression.fastq_second} "
                f"from sample {sample_id} are already in Housekeeper"
            )
        if not result:
            LOG.warning("Files were not added to fastq!")

    @staticmethod
    def are_fastqs_in_housekeeper(compression: CompressionData, fastq_files: dict[Path, File]):
        return compression.fastq_first in fastq_files and compression.fastq_second in fastq_files

"""API to prepare fastq files for analysis"""

import logging
import os
from pathlib import Path
from typing import Dict, List

from cg.apps.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.compress import files
from cg.meta.compress.compress import CompressAPI
from cg.models import CompressionData
from cg.store import Store, models
from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)


class PrepareFastqAPI:
    def __init__(self, store: Store, compress_api: CompressAPI):
        self.store: Store = store
        self.hk_api: HousekeeperAPI = compress_api.hk_api
        self.compress_api: CompressAPI = compress_api
        self.crunchy_api: CrunchyAPI = compress_api.crunchy_api

    def get_compression_objects(self, case_id: str) -> List[CompressionData]:
        """Return a list of compression objects"""
        case_obj: models.Family = self.store.family(case_id)
        compression_objects = []
        for link in case_obj.links:
            sample_id = link.sample.internal_id
            version_obj = self.compress_api.get_latest_version(sample_id)
            compression_objects.extend(files.get_spring_paths(version_obj))
        return compression_objects

    def is_spring_decompression_needed(self, case_id: str) -> bool:
        """Check if spring decompression needs to be started"""
        compression_objects = self.get_compression_objects(case_id=case_id)
        for compression_object in compression_objects:
            if (
                self.crunchy_api.is_compression_pending(compression_object)
                or compression_object.pair_exists()
            ):
                continue
            return True
        return False

    def is_spring_decompression_running(self, case_id: str) -> bool:
        """Check if case is being decompressed"""
        compression_objects = self.get_compression_objects(case_id=case_id)
        return any(
            self.crunchy_api.is_compression_pending(compression_object)
            for compression_object in compression_objects
        )

    def can_at_least_one_sample_be_decompressed(self, case_id: str) -> bool:
        """Returns True if at least one sample can be decompressed, otherwise False"""
        compression_objects: List[CompressionData] = self.get_compression_objects(case_id=case_id)
        return any(
            self.crunchy_api.is_spring_decompression_possible(compression_object)
            for compression_object in compression_objects
        )

    def can_at_least_one_decompression_job_start(self, case_id: str, dry_run: bool) -> bool:
        """Returns True if decompression started for at least one sample, otherwise False"""
        case_obj: models.Family = self.store.family(case_id)
        link: models.FamilySample
        did_something_start = False
        for link in case_obj.links:
            sample_id = link.sample.internal_id
            if dry_run:
                LOG.info(
                    f"This is a dry run, therefore decompression for {sample_id} won't be started"
                )
                continue
            decompression_started = self.compress_api.decompress_spring(sample_id)
            if decompression_started:
                did_something_start = True
        return did_something_start

    def check_fastq_links(self, case_id: str) -> None:
        """Check if all fastq files are linked in housekeeper"""
        case_obj: models.Family = self.store.family(case_id)
        for link in case_obj.links:
            sample_id = link.sample.internal_id
            version_obj: hk_models.Version = self.compress_api.get_latest_version(sample_id)
            fastq_files: Dict[Path, hk_models.File] = files.get_hk_files_dict(
                tags=["fastq"], version_obj=version_obj
            )
            compression_objs: List[CompressionData] = files.get_spring_paths(version_obj)
            for compression_obj in compression_objs:
                if compression_obj.fastq_first not in fastq_files:
                    self.compress_api.add_decompressed_fastq(sample_id)
                if compression_obj.fastq_second not in fastq_files:
                    self.compress_api.add_decompressed_fastq(sample_id)

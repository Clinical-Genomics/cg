"""API to prepare fastq files for analysis"""

import logging
import os
from typing import Dict
from pathlib import Path

from cg.meta.compress.compress import CompressAPI
from cg.apps.crunchy import CrunchyAPI
from cg.meta.compress import files
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.store import Store
from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)


class PrepareFastqAPI:
    def __init__(self, store: Store, compress_api: CompressAPI):
        self.store = store
        self.hk_api: HousekeeperAPI = compress_api.hk_api
        self.compress_api: CompressAPI = compress_api
        self.crunchy_api: CrunchyAPI = compress_api.crunchy_api

    def is_spring_decompression_needed(self, case_id: str) -> bool:
        """Check if spring decompression is needed"""
        case_obj = self.store.family(case_id)
        for link in case_obj.links:
            sample_id = link.sample.internal_id
            version_obj = self.compress_api.get_latest_version(sample_id)
            compression_objects = files.get_spring_paths(version_obj)
            for compression_object in compression_objects:
                if self.crunchy_api.is_compression_pending(compression_object):
                    continue
                if compression_object.pair_exists():
                    continue
                return True
        return False

    def start_spring_decompression(self, case_id: str, dry_run: bool) -> bool:
        """Starts spring decompression"""
        case_obj = self.store.family(case_id)
        for link in case_obj.links:
            sample_id = link.sample.internal_id
            version_obj = self.compress_api.get_latest_version(sample_id)
            compression_objs = files.get_spring_paths(version_obj)
            for compr_obj in compression_objs:
                if not self.crunchy_api.is_spring_decompression_possible(compr_obj):
                    return False
        for link in case_obj.links:
            sample_id = link.sample.internal_id
            if dry_run:
                LOG.info(
                    f"This is a dry run, therefore decompression for {sample_id} won't be started"
                )
                return True
            decompression_started = self.compress_api.decompress_spring(sample_id)
            if not decompression_started:
                return False
        return True

    def check_fastq_links(self, case_id: str) -> bool:
        """Check if all fastq files are linked in housekeeper"""
        case_obj = self.store.family(case_id)
        for link in case_obj.links:
            sample_id = link.sample.internal_id
            version_obj: hk_models.Version = self.compress_api.get_latest_version(sample_id)
            fastq_files: Dict[Path, hk_models.File] = files.get_hk_files_dict(
                tags=["fastq"], version_obj=version_obj
            )
            compression_objs = files.get_spring_paths(version_obj)
            for compr_obj in compression_objs:
                if compr_obj.fastq_first not in fastq_files:
                    self.compress_api.add_decompressed_fastq(sample_id)
                    return False
                if compr_obj.fastq_second not in fastq_files:
                    self.compress_api.add_decompressed_fastq(sample_id)
                    return False
        return True

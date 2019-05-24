# -*- coding: utf-8 -*-
"""
This module handles concatenation of usalt fastq files.

Classes:
    FastqFileNameCreator: Creates valid usalt filenames
    FastqHandler: Handles fastq file linking
"""
import logging
from typing import List

from cg.apps import tb
from cg.store import Store
from cg.apps.pipelines.fastqhandler import BaseFastqHandler

LOGGER = logging.getLogger(__name__)


class MipFastqHandler(BaseFastqHandler):
    """Handles fastq file linking"""

    def __init__(self, config, db: Store, tb_api: tb.TrailblazerAPI):
        self.tb = tb_api
        self.config = config
        self.db = db

    def link(self, case: str, sample: str, files: List):
        """Link FASTQ files for a pipeline sample."""

        # determine link between famliy and sample

        sample_obj = self.db.sample(internal_id=sample)

        self.tb.link(
            family=case,
            sample=sample,
            analysis_type=sample_obj.application_version.application.analysis_type,
            files=files,
        )

# -*- coding: utf-8 -*-
"""
This module handles concatenation of usalt fastq files.

Classes:
    FastqFileNameCreator: Creates valid usalt filenames
    FastqHandler: Handles fastq file linking
"""
import logging
import os
from pathlib import Path
from typing import List

from cg.apps.pipelines.fastqhandler import BaseFastqHandler

LOGGER = logging.getLogger(__name__)


class USaltFastqHandler(BaseFastqHandler):
    """Handles fastq file linking"""

    class USaltFastqFileNameCreator(BaseFastqHandler.BaseFastqFileNameCreator):
        """Creates valid usalt filename from the parameters"""

        @staticmethod
        def create(lane: str, flowcell: str, sample: str, read: str,
                   undetermined: bool = False) -> str:
            """Name a FASTQ file following usalt conventions. Naming must be
            xxx_R_1.fastq.gz and xxx_R_2.fastq.gz"""

            # ACC1234A1_FCAB1ABC2_L1_1.fastq.gz sample_flowcell_lane_read.fastq.gz
            flowcell = f"{flowcell}-undetermined" if undetermined else flowcell
            return f"{sample}_{flowcell}_L{lane}_{read}.fastq.gz"

    def __init__(self, config):
        self.root_dir = config['usalt']['root']


    def link(self, case: str, sample: str, files: List):
        """Link FASTQ files for a usalt sample.
        Shall be linked to /<usalt root directory>/case-id/fastq/"""

        # The fastq files should be linked to /.../fastq/<project>/<sample>/*.fastq.gz.
        wrk_dir = Path(self.root_dir) / 'fastq' / case / sample

        wrk_dir.mkdir(parents=True, exist_ok=True)

        linked_reads_paths = {1: [], 2: []}

        for fastq_data in files:
            original_fastq_path = Path(fastq_data['path'])
            linked_fastq_name = FastqFileNameCreator.create(
                lane=fastq_data['lane'],
                flowcell=fastq_data['flowcell'],
                sample=sample,
                read=fastq_data['read'],
                undetermined=fastq_data['undetermined'],
            )
            linked_fastq_path = wrk_dir / linked_fastq_name
            linked_reads_paths[fastq_data['read']].append(linked_fastq_path)

            if not linked_fastq_path.exists():
                logger.info(f"linking: %s -> %s", original_fastq_path, linked_fastq_path)
                linked_fastq_path.symlink_to(original_fastq_path)
            else:
                logger.debug(f"destination path already exists: %s", linked_fastq_path)

    @staticmethod
    def _remove_files(files):
        for file in files:
            if os.path.isfile(file):
                os.remove(file)

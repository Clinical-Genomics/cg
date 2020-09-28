"""
This module handles concatenation of usalt fastq files.

Classes:
    FastqFileNameCreator: Creates valid usalt filenames
    FastqHandler: Handles fastq file linking
"""
import logging
from pathlib import Path
from typing import List

from cg.apps.pipelines.fastqhandler import BaseFastqHandler

LOGGER = logging.getLogger(__name__)


class FastqHandler(BaseFastqHandler):
    """Handles fastq file linking"""

    class FastqFileNameCreator(BaseFastqHandler.BaseFastqFileNameCreator):
        """Creates valid usalt filename from the parameters"""

        @staticmethod
        def create(lane: str, flowcell: str, sample: str, read: str, more: dict = None) -> str:
            """Name a FASTQ file following usalt conventions. Naming must be
            xxx_R_1.fastq.gz and xxx_R_2.fastq.gz"""

            undetermined = more.get("undetermined", None)

            # ACC1234A1_FCAB1ABC2_L1_1.fastq.gz sample_flowcell_lane_read.fastq.gz
            flowcell = f"{flowcell}-undetermined" if undetermined else flowcell
            return f"{sample}_{flowcell}_L{lane}_{read}.fastq.gz"

    def __init__(self, config):
        super().__init__(config)
        self.root_dir = config["microsalt"]["root"]

    def link(self, ticket: int, sample: str, files: List[dict]) -> None:
        """Link FASTQ files for a usalt sample.
        Shall be linked to /<usalt root directory>/ticket/fastq/"""

        # The fastq files should be linked to /.../fastq/<ticket>/<sample>/*.fastq.gz.
        wrk_dir = Path(self.root_dir) / "fastq" / str(ticket) / sample

        wrk_dir.mkdir(parents=True, exist_ok=True)

        for fastq_data in files:
            original_fastq_path = Path(fastq_data["path"])
            linked_fastq_name = self.FastqFileNameCreator.create(
                lane=fastq_data["lane"],
                flowcell=fastq_data["flowcell"],
                sample=sample,
                read=fastq_data["read"],
                more={"undetermined": fastq_data["undetermined"]},
            )
            linked_fastq_path = wrk_dir / linked_fastq_name

            if not linked_fastq_path.exists():
                LOGGER.info("linking: %s -> %s", original_fastq_path, linked_fastq_path)
                linked_fastq_path.symlink_to(original_fastq_path)
            else:
                LOGGER.debug("destination path already exists: %s", linked_fastq_path)

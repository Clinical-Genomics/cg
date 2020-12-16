import logging
from pathlib import Path
from typing import Optional

from cg.utils.commands import Process

from .models import CGDeliverables

LOG = logging.getLogger(__name__)


class HermesApi:
    """Class to communicate with hermes"""

    def __init__(self, config: dict):
        self.process = Process(config["hermes"]["binary_path"])
        self.dry_run: bool = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Update dry run"""
        LOG.info("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    def convert_deliverables(
        self, deliverables_file: Path, pipeline: str, analysis_type: Optional[str] = None
    ) -> CGDeliverables:
        """Convert deliverables file in raw pipeline format to CG format with hermes"""
        LOG.info("Converting pipeline deliverables to CG deliverables")
        convert_command = [
            "convert",
            "deliverables",
            "--pipeline",
            pipeline,
            str(deliverables_file),
        ]
        if analysis_type:
            convert_command.extend(["--analysis-type", analysis_type])
        self.process.run_command(convert_command)

        return CGDeliverables.parse_raw(self.process.stdout)

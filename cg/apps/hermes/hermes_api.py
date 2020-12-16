import logging
from pathlib import Path
from typing import Optional

from cg.constants.constants import Pipeline
from cg.utils.commands import Process

from .models import CGDeliverables

LOG = logging.getLogger(__name__)


class HermesApi:
    """Class to communicate with hermes"""

    def __init__(self, config: dict, pipeline: Pipeline, analysis_type: Optional[str] = None):
        self.process = Process(config["hermes"]["binary_path"])
        self.dry_run: bool = False
        self.pipeline: Pipeline = pipeline
        self.analysis_type = analysis_type

    def set_dry_run(self, dry_run: bool) -> None:
        """Update dry run"""
        LOG.info("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    def convert_deliverables(self, deliverables_file: Path) -> CGDeliverables:
        """Convert deliverables file in raw pipeline format to CG format with hermes"""
        convert_command = [
            "convert",
            "deliverables",
            "--pipeline",
            str(self.pipeline),
            str(deliverables_file),
        ]
        if self.analysis_type:
            convert_command.extend(["--analysis-type", self.analysis_type])
        self.process.run_command(convert_command)

        return CGDeliverables.parse_raw(self.process.stdout)

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from cg.apps.housekeeper import models as hk_models
from cg.utils.commands import Process

from .models import CGDeliverables

LOG = logging.getLogger(__name__)


class HermesApi:
    """Class to communicate with hermes"""

    def __init__(self, config: dict):
        self.process = Process(config["hermes"]["binary_path"])

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

    def create_housekeeper_bundle(
        self,
        bundle_name: str,
        deliverables: Path,
        pipeline: str,
        analysis_type: Optional[str],
        created: Optional[datetime],
    ) -> hk_models.InputBundle:
        """Convert pipeline deliverables to housekeeper bundle ready to be inserted into hk"""
        cg_deliverables: CGDeliverables = self.convert_deliverables(
            deliverables_file=deliverables, pipeline=pipeline, analysis_type=analysis_type
        )
        return self.get_housekeeper_bundle(
            deliverables=cg_deliverables, created=created, bundle_name=bundle_name
        )

    @staticmethod
    def get_housekeeper_bundle(
        deliverables: CGDeliverables, bundle_name: str, created: Optional[datetime] = None
    ) -> hk_models.InputBundle:
        """Convert a deliverables object to a housekeeper object"""
        bundle_info = {
            "name": bundle_name,
            "files": [file_info.dict() for file_info in deliverables.files],
        }
        if created:
            bundle_info["created"] = created

        return hk_models.InputBundle(**bundle_info)

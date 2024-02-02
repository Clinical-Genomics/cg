import logging
from datetime import datetime
from pathlib import Path

from cg.apps.housekeeper import models as hk_models
from cg.utils.commands import Process

from .models import CGDeliverables

LOG = logging.getLogger(__name__)


class HermesApi:
    """Class to communicate with hermes"""

    def __init__(self, config: dict):
        self.process = Process(binary=config["hermes"]["binary_path"])

    def convert_deliverables(
        self, deliverables_file: Path, workflow: str, analysis_type: str | None = None
    ) -> CGDeliverables:
        """Convert deliverables file in raw workflow format to CG format with hermes"""
        LOG.info("Converting workflow deliverables to CG deliverables")
        convert_command = [
            "convert",
            "deliverables",
            "--pipeline",
            workflow,
            str(deliverables_file),
        ]
        if analysis_type:
            convert_command.extend(["--analysis-type", analysis_type])
        self.process.run_command(convert_command)

        return CGDeliverables.model_validate_json(self.process.stdout)

    def create_housekeeper_bundle(
        self,
        bundle_name: str,
        deliverables: Path,
        workflow: str,
        analysis_type: str | None,
        created: datetime | None,
    ) -> hk_models.InputBundle:
        """Convert workflow deliverables to a Housekeeper bundle ready to be inserted into Housekeeper."""
        cg_deliverables: CGDeliverables = self.convert_deliverables(
            deliverables_file=deliverables, workflow=workflow, analysis_type=analysis_type
        )
        return self.get_housekeeper_bundle(
            deliverables=cg_deliverables, created=created, bundle_name=bundle_name
        )

    @staticmethod
    def get_housekeeper_bundle(
        deliverables: CGDeliverables, bundle_name: str, created: datetime | None = None
    ) -> hk_models.InputBundle:
        """Convert a deliverables object to a housekeeper object"""
        bundle_info = {
            "name": bundle_name,
            "files": [file_info.model_dump() for file_info in deliverables.files],
        }
        if created:
            bundle_info["created"] = created

        return hk_models.InputBundle(**bundle_info)

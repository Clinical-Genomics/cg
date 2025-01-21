import logging
from datetime import datetime
from pathlib import Path

from cg.apps.housekeeper import models as hk_models
from cg.io.json import read_json_stream, write_json_stream
from cg.utils.commands import Process

from .models import CGDeliverables

LOG = logging.getLogger(__name__)


class HermesApi:
    """Class to communicate with hermes"""

    def __init__(self, config: dict):
        self.process = Process(
            binary=config["hermes"]["binary_path"],
        )
        self.container_path: str = config["hermes"]["container_path"]
        self.container_mount_volume = config["hermes"]["container_mount_volume"]

    def convert_deliverables(
        self,
        deliverables_file: Path,
        workflow: str,
        analysis_type: str | None = None,
        force: bool = False,
    ) -> CGDeliverables:
        """Convert deliverables file in raw workflow format to CG format with Hermes."""
        LOG.info("Converting workflow deliverables to CG deliverables")
        convert_command = [
            "run",
            "--bind",
            self.container_mount_volume,
            self.container_path,
            "convert",
            "deliverables",
            "--workflow",
            workflow,
            str(deliverables_file),
        ]
        if analysis_type:
            convert_command.extend(["--analysis-type", analysis_type])
        if force:
            convert_command.append("--force")
        self.process.run_command(convert_command)
        json_stream: str = self.process.stdout
        if force:
            data: dict[str, any] = read_json_stream(json_stream)
            for file_tag in data["files"]:
                file_tag["mandatory"] = False
            json_stream: str = write_json_stream(data)
        return CGDeliverables.model_validate_json(json_stream)

    def create_housekeeper_bundle(
        self,
        bundle_name: str,
        deliverables: Path,
        workflow: str,
        analysis_type: str | None,
        created: datetime | None,
        force: bool = False,
    ) -> hk_models.InputBundle:
        """Convert workflow deliverables to a Housekeeper bundle ready to be inserted into Housekeeper."""
        cg_deliverables: CGDeliverables = self.convert_deliverables(
            deliverables_file=deliverables,
            workflow=workflow,
            analysis_type=analysis_type,
            force=force,
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

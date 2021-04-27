import logging
from pathlib import Path

from cg.meta.demultiplex import files
from cg.models.demultiplex.demux_results import DemuxResults

LOG = logging.getLogger(__name__)


class DemuxPostProcessingAPI:
    def __init__(self):
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        LOG.debug("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    def rename_files(self, demux_results: DemuxResults) -> None:
        """Rename the files according to how we want to have it after demultiplexing is ready"""
        flowcell_id: str = demux_results.flowcell.flowcell_id
        for project_dir in demux_results.raw_projects:
            if "index" in project_dir.name:
                continue
            files.rename_project_directory(
                project_directory=project_dir, flowcell_id=flowcell_id, dry_run=self.dry_run
            )

    def add_to_cgstats(self) -> None:
        """Add the information from demultiplexing to cgstats"""
        pass

    def create_cgstats_reports(self) -> None:
        """Create a report for every sample that was demultiplexed"""

# This module is to remove the traces of a flowcell from statusdb as well as housekeeper.
# Furthermore it should remove the demultiplexed-runs directory and SampleSheet to finally restart flowcells from a clean slate

import click
import logging

from pathlib import Path
from typing import List

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.cgstats.stats import StatsAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.command("wipe")
@click.option("--dry-run", is_flag=True, help="Set the cleaning process to run in dry-run mode")
@click.option("-y", "--yes", is_flag=True, help="Pass all checks, use with care!")
@click.pass_context
def clean_flowcell(context: CGConfig, dry_run: bool, yes: bool):
    """
    Before start of demultiplexing workflow, clean all traces of a flowcell in Statusdb, Housekeeper,
    and Demultiplexed-runs
    """

    pass


class WipeDemuxAPI:
    """Class to handle wiping out a flowcell before restart/start"""

    def __init__(
        self, flowcell_id: str, root_dir: Path, status_db: Store, housekeeper_api: HousekeeperAPI
    ):
        self.dry_run = True
        self.exit_code = EXIT_SUCCESS
        self.flowcell_id = flowcell_id
        self.housekeeper_api = housekeeper_api
        self.root_dir = root_dir
        self.status_db = status_db

    def set_fail(self) -> None:
        """Set exit code to EXIT_FAIL"""
        self.exit_code = EXIT_FAIL

    def set_success(self) -> None:
        """Set exit code to EXIT_SUCCESS"""
        self.exit_code = EXIT_SUCCESS

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run flag for API"""
        self.dry_run = dry_run

    def wipe_flowcell_housekeeper(self, housekeeper_api: HousekeeperAPI, status_db: Store) -> None:
        """Wipe any presence of a flowcell in housekeeper. Including Sample sheets AND fastq-files"""
        self._wipe_flowcell_tag_housekeeper()

    def _wipe_flowcell_tag_housekeeper(self) -> None:
        """Wipe the presence of a flowcell, based on the flowcell id as a tag, in Housekeeper."""
        self.set_success()
        if self.housekeeper_api.check_for_files(tags=[self.flowcell_id]):
            self.housekeeper_api.delete_files(dry_run=self.dry_run, tags=[self.flowcell_id])
            return
        self.set_fail()

    def _wipe_fastq_tags_housekeeper(self, samples: List[str]) -> None:
        """Wipe the presence of a flowcell, based on samples related to flowcell and the fastq-tags, in Housekeeper."""
        self.set_success()
        samples_to_delete = []

        for sample in samples:
            if self.housekeeper_api.check_for_files(tags=["fastq"]):
                samples_to_delete.append(sample)
            else:
                LOG.warning(f"No fastq-files for {sample} were found in Housekeeper.")
                self.set_fail()

        if samples_to_delete and self.exit_code == EXIT_SUCCESS:
            for sample in samples_to_delete:
                self.housekeeper_api.delete_files(
                    dry_run=self.dry_run, tags=["fastq"], bundle=sample
                )

    def wipe_flowcell_statusdb(self, status_db: Store) -> None:
        """Wipe any prescense of a flowcell in status db"""
        status_db.flowcell(self.flowcell_id)
        pass

    def wipe_flowcell_cgstats(self, cgstats: StatsAPI) -> None:
        """Wipe ay presence of a flowcell in cgstats"""
        pass

    def clean_flowcell_hasta(self, demultiplex_api: DemultiplexingAPI, flowcell_id: str) -> None:
        # Get path to out from demux, clean the path. Check there is a path for flowcell.
        pass

    def active_samples_on_flowcell(self) -> bool:
        """Check if there are any active cases related to samples of a flowcell"""
        if any(
            [
                self.status_db.active_sample(internal_id=sample.sample_id)
                for sample in self.status_db.flowcell(name=self.flowcell_id).samples
            ]
        ):
            return True
        else:
            return False

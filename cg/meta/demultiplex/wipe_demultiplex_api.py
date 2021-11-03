import logging

from pathlib import Path
from shutil import rmtree
from typing import List, Optional

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.cgstats.stats import StatsAPI
from cg.exc import WipeDemuxError
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Sample

log = logging.getLogger(__name__)


class WipeDemuxAPI:
    """Class to handle wiping out a flowcell before restart/start"""

    def __init__(self, config: CGConfig, demultiplexing_dir: Path, run_name: str):
        self.dry_run: bool = True
        self.demultiplexing_dir: Path = demultiplexing_dir
        self.flow_cell_name: str = ""
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.run_name: str = run_name
        self.status_db: Store = config.status_db
        self.stats_api: StatsAPI = config.cg_stats_api
        self.parse_flowcell_name()
        self.in_status_db: bool = self._get_presence_status_status_db()
        self._get_samples_on_flow_cell()
        log.debug("WipeDemuxAPI: API initiated")

    def parse_flowcell_name(self) -> None:
        """Parse flowcell name from flowcell run name

        This will assume that the flowcell naming convention is used.
        Convention is: <date>_<machine>_<run_numbers>_<A|B><flowcell_id>
        Example: 201203_A00689_0200_AHVKJCDRXX
        """
        split_name: List[str] = self.run_name.split("_")
        base_name: str = split_name[-1]
        self.flow_cell_name: str = base_name[1:]
        log.debug("WipeDemuxAPI: Set flowcell id to %s", base_name[1:])

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run flag for API"""
        log.debug(f"WipeDemuxAPI: Setting dry run mode to: {dry_run}")
        self.dry_run = dry_run

    def _get_presence_status_status_db(self) -> bool:
        """Update about the presence of given flowcell in status_db"""
        if self.status_db.flowcell(self.flow_cell_name):
            return True
        else:
            return False

    def _get_samples_on_flow_cell(self):
        """Return a list of samples related to a flowcell from status-db"""
        if self.in_status_db:
            self.samples_on_flow_cell: List[Sample] = self.status_db.flowcell(
                name=self.flow_cell_name
            ).samples

    def active_samples_on_flow_cell(self) -> Optional[List[str]]:
        """Check if there are any active cases related to samples of a flowcell"""
        active_samples_on_flow_cell = [
            sample.internal_id
            for sample in self.samples_on_flow_cell
            if self.status_db.active_sample(internal_id=sample.sample_id)
        ]
        if active_samples_on_flow_cell:
            return active_samples_on_flow_cell

    def _wipe_flow_cell_tag_housekeeper(self) -> None:
        """Wipe the presence of a flowcell, based on the flowcell id as a tag, in Housekeeper."""
        if self.housekeeper_api.check_for_files(tags=[self.flow_cell_name]):
            self.housekeeper_api.delete_files(dry_run=self.dry_run, tags=[self.flow_cell_name])
            return

        log.info(f"Housekeeper: No files with tag: {self.flow_cell_name}")

    def _wipe_fastq_tags_housekeeper(self) -> None:
        """Wipe the presence of a flowcell, based on samples related to flowcell and the fastq-tags, in Housekeeper."""
        samples_to_delete = []

        if self.in_status_db:
            for sample in self.samples_on_flow_cell:
                if self.housekeeper_api.check_for_files(bundle=sample.internal_id, tags=["fastq"]):
                    samples_to_delete.append(sample)
                else:
                    log.info(f"Housekeeper: No fastq-files for {sample} were found in Housekeeper.")

            if samples_to_delete:
                for sample in samples_to_delete:
                    self.housekeeper_api.delete_files(
                        dry_run=self.dry_run, tags=["fastq"], bundle=sample.internal_id
                    )
            else:
                log.info("Housekeeper: There where files for samples connected to the flowcell")

    def wipe_flow_cell_housekeeper(self) -> None:
        """Wipe any presence of a flowcell in housekeeper. Including Sample sheets AND fastq-files"""

        log.info(f"Housekeeper: Wiping files with tag {self.flow_cell_name}")
        self._wipe_flow_cell_tag_housekeeper()
        log.info(f"Housekeeper: Wiping files on sample bundles with fastq-tag")
        self._wipe_fastq_tags_housekeeper()

    def wipe_flow_cell_statusdb(self) -> None:
        """Wipe any prescense of a flowcell in status-db"""
        if self.dry_run:
            log.info(f"StatusDB: Would remove {self.flow_cell_name}")
        else:
            log.info(f"StatusDB: Wiping flowcell {self.flow_cell_name}")
            self.status_db.delete_flowcell(flowcell_name=self.flow_cell_name)

    def wipe_flow_cell_cgstats(self) -> None:
        """Wipe ay presence of a flowcell in cgstats"""
        from cg.apps.cgstats.crud.delete import delete_flowcell

        if self.dry_run:
            log.info(f"CGStats: Would remove {self.flow_cell_name}")
        else:
            delete_flowcell(manager=self.stats_api, flowcell_name=self.flow_cell_name)

    def wipe_flow_cell_demultiplex_dir(self) -> None:
        """Remove demultiplexing directory set by DemultiplexingAPI"""
        out_dir: Path = self.demultiplexing_dir.joinpath(self.run_name)
        if out_dir.exists():
            if self.dry_run:
                log.info(f"Hasta: Would remove the following directory {out_dir.as_posix()}")
            else:
                log.info(f"Hasta: Removing flowcell directory {out_dir.as_posix()}")
                rmtree(path=out_dir)
        else:
            log.info(f"Hasta: No target demultiplexing directory {out_dir.as_posix()}")

    def wipe_flow_cell(self) -> None:
        """Master command to completely wipe the presence of a flowcell in all services"""
        if self.in_status_db:
            active_samples_on_flow_cell: List[str] = self.active_samples_on_flow_cell()
            if active_samples_on_flow_cell:
                log.warning(
                    f"There are active analyses using data from this flowcell.\n"
                    f"Before restarting the demultiplexing process - please cancel the ongoing analyses of the following"
                    f"sample(s): \n{active_samples_on_flow_cell}"
                )
                raise WipeDemuxError
        else:
            self.wipe_flow_cell_cgstats()
            self.wipe_flow_cell_demultiplex_dir()
            self.wipe_flow_cell_housekeeper()
            self.wipe_flow_cell_statusdb()

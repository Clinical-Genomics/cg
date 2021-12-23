import logging

from pathlib import Path
from shutil import rmtree
from typing import Iterable, List, Optional

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.cgstats.stats import StatsAPI
from cg.exc import WipeDemuxError
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Sample, Flowcell
from housekeeper.store.models import File

log = logging.getLogger(__name__)


class WipeDemuxAPI:
    """Class to handle wiping out a flow cell before restart/start"""

    def __init__(self, config: CGConfig, demultiplexing_dir: Path, run_name: str):
        self.dry_run: bool = True
        self.demultiplexing_dir: Path = demultiplexing_dir
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.run_name: Path = Path(run_name)
        self.status_db: Store = config.status_db
        self.stats_api: StatsAPI = config.cg_stats_api
        self.samples_on_flow_cell: List[Sample] = []
        log.debug("WipeDemuxAPI: API initiated")

    @property
    def demultiplexing_run_path(self) -> Path:
        """Return the demultiplexing directory path for the given run name"""
        return self.demultiplexing_dir.joinpath(self.run_name)

    @property
    def flow_cell_name(self) -> str:
        """Parse flow cell name from flowcell run name

        This will assume that the flow cell naming convention is used.
        Convention is: <date>_<machine>_<run_numbers>_<A|B><flowcell_id>
        Example: 201203_A00689_0200_AHVKJCDRXX
        """
        return self.run_name.name.split("_")[-1][1:]

    @property
    def status_db_presence(self) -> bool:
        """Update about the presence of given flow cell in status_db"""
        presence = (
            self.status_db.query(Flowcell).filter(Flowcell.name == self.flow_cell_name).first()
        )
        if presence:
            return True
        else:
            return False

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run flag for API"""
        log.debug(f"WipeDemuxAPI: Setting dry run mode to {dry_run}")
        self.dry_run = dry_run

    def _set_samples_on_flow_cell(self) -> None:
        """Set a list of samples related to a flow cell in status-db"""
        self.samples_on_flow_cell: List[Sample] = (
            self.status_db.query(Flowcell)
            .filter(Flowcell.name == self.flow_cell_name)
            .first()
            .samples
        )

    def active_samples_on_flow_cell(self) -> Optional[List[str]]:
        """Check if there are any active cases related to samples of a flow cell"""
        active_samples_on_flow_cell = [
            sample.internal_id
            for sample in self.samples_on_flow_cell
            if self.status_db.active_sample(internal_id=sample.internal_id)
        ]
        if active_samples_on_flow_cell:
            return active_samples_on_flow_cell

    def _wipe_sample_sheet_housekeeper(self) -> None:
        """Wipe the presence of all sample sheets related to a flow cell in Housekeeper."""
        sample_sheet_files: Iterable[File] = self.housekeeper_api.files(
            tags=[self.flow_cell_name, "samplesheet"]
        )
        if any(sample_sheet_files):
            for file in sample_sheet_files:
                self.housekeeper_api.delete_file(file_id=file.id)
                log.info(f"Housekeeper: Wiped {file.path} from housekeeper")
        else:
            log.info(f"Housekeeper: No files found with tag: {self.flow_cell_name}")

    def _wipe_fastq_and_spring_housekeeper(self) -> None:
        """Wipe the presence of any spring/fastq files in Housekeeper related to samples on the flow cell"""

        for sample in self.samples_on_flow_cell:
            self.housekeeper_api.delete_fastq_and_spring(
                bundle=sample.internal_id, demultiplexing_path=self.demultiplexing_run_path
            )

    def wipe_flow_cell_housekeeper(self) -> None:
        """Wipe any presence of a flow cell in housekeeper. Including Sample sheets AND fastq-files"""

        log.info(f"Housekeeper: Wiping sample sheet files with tag {self.flow_cell_name}")
        self._wipe_sample_sheet_housekeeper()
        log.info(f"Housekeeper: Wiping fastq and spring files related to flowcell")
        self._wipe_fastq_and_spring_housekeeper()

    def wipe_flow_cell_statusdb(self) -> None:
        """Wipe any presence of a flow cell in status-db"""
        if self.dry_run:
            log.info(f"StatusDB: Would remove {self.flow_cell_name}")
        else:
            log.info(f"StatusDB: Wiping flowcell {self.flow_cell_name}")
            self.status_db.delete_flowcell(flowcell_name=self.flow_cell_name)

    def wipe_flow_cell_cgstats(self) -> None:
        """Wipe ay presence of a flow cell in cgstats"""
        from cg.apps.cgstats.crud.delete import delete_flowcell

        if self.dry_run:
            log.info(f"CGStats: Would remove {self.flow_cell_name}")
        else:
            delete_flowcell(manager=self.stats_api, flowcell_name=self.flow_cell_name)

    def wipe_flow_cell_demultiplex_dir(self) -> None:
        """Wipe demultiplexing directory on the server"""
        out_dir: Path = self.demultiplexing_dir.joinpath(self.run_name.name)
        if out_dir.exists():
            if self.dry_run:
                log.info(f"Hasta: Would remove the following directory {out_dir.as_posix()}")
            else:
                log.info(f"Hasta: Removing flow cell directory {out_dir.as_posix()}")
                rmtree(path=out_dir)
        else:
            log.info(f"Hasta: No target demultiplexing directory {out_dir.as_posix()}")

    def wipe_flow_cell(
        self,
        skip_cg_stats: bool = False,
        skip_demultiplexing_dir: bool = False,
        skip_housekeeper: bool = False,
        skip_status_db: bool = False,
    ) -> None:
        """Master command to completely wipe the presence of a flowcell in all services"""
        if self.status_db_presence:
            self._set_samples_on_flow_cell()
            active_samples_on_flow_cell: List[str] = self.active_samples_on_flow_cell()
            if active_samples_on_flow_cell:
                log.warning(
                    f"There are active analyses using data from this flowcell.\n"
                    f"Before restarting the demultiplexing process - please cancel the ongoing analyses of the "
                    f"following sample(s): \n{active_samples_on_flow_cell}"
                )
                raise WipeDemuxError
        else:
            if not skip_cg_stats:
                self.wipe_flow_cell_cgstats()
            if not skip_demultiplexing_dir:
                self.wipe_flow_cell_demultiplex_dir()
            if not skip_housekeeper:
                self.wipe_flow_cell_housekeeper()
            if not skip_status_db:
                self.wipe_flow_cell_statusdb()

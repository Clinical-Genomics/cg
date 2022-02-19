import logging
import shutil

from glob import glob
from pathlib import Path
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

    def __init__(self, config: CGConfig, demultiplexing_dir: Path, dry_run: bool, run_path: str):
        self.dry_run: bool = self.set_dry_run(dry_run=dry_run)
        self.demultiplexing_dir: Path = demultiplexing_dir
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.run_path: Path = Path(run_path)
        self.status_db: Store = config.status_db
        self.stats_api: StatsAPI = config.cg_stats_api
        self.samples_on_flow_cell: List[Sample] = []
        log.debug("WipeDemuxAPI: API initiated")

    @property
    def demultiplexing_path(self) -> Path:
        """Return the demultiplexing directory path for the given run name"""
        return self.demultiplexing_dir.joinpath(self.run_path.name)

    @property
    def flow_cell_name(self) -> str:
        """Parse flow cell name from flowcell run name

        This will assume that the flow cell naming convention is used.
        Convention is: <date>_<machine>_<run_numbers>_<A|B><flowcell_id>
        Example: 201203_A00689_0200_AHVKJCDRXX
        """
        return self.run_path.name.split("_")[-1][1:]

    @property
    def status_db_presence(self) -> bool:
        """Update about the presence of given flow cell in status_db"""
        return bool(
            self.status_db.query(Flowcell).filter(Flowcell.name == self.flow_cell_name).first()
        )

    @staticmethod
    def set_dry_run(dry_run: bool) -> bool:
        """Set dry run flag for API"""
        log.debug(f"WipeDemuxAPI: Setting dry run mode to {dry_run}")
        return dry_run

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
        active_samples_on_flow_cell: List[str] = [
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
                log.info(f"WipeDemuxAPI-Housekeeper: Wiped {file.path} from housekeeper")
        else:
            log.info(f"WipeDemuxAPI-Housekeeper: No files found with tag: {self.flow_cell_name}")

    def _wipe_fastq_and_spring_housekeeper(self) -> None:
        """Wipe the presence of any spring/fastq files in Housekeeper related to samples on the flow cell"""

        for sample in self.samples_on_flow_cell:
            self.housekeeper_api.delete_fastq_and_spring(
                bundle=sample.internal_id, demultiplexing_path=self.demultiplexing_path
            )

    def wipe_flow_cell_housekeeper(self) -> None:
        """Wipe any presence of a flow cell in housekeeper. Including Sample sheets AND fastq-files"""

        log.info(
            f"WipeDemuxAPI-Housekeeper: Wiping sample sheet files with tag {self.flow_cell_name}"
        )
        self._wipe_sample_sheet_housekeeper()
        log.info(
            f"WipeDemuxAPI-Housekeeper: Wiping fastq and spring files related to flowcell {self.flow_cell_name}"
        )
        self._wipe_fastq_and_spring_housekeeper()

    def wipe_flow_cell_statusdb(self) -> None:
        """Wipe any presence of a flow cell in status-db"""
        if self.dry_run:
            log.info(f"WipeDemuxAPI-StatusDB: Would remove {self.flow_cell_name}")
        else:
            log.info(f"WipeDemuxAPI-StatusDB: Wiping flowcell {self.flow_cell_name}")
            self.status_db.delete_flowcell(flowcell_name=self.flow_cell_name)

    def wipe_flow_cell_cgstats(self) -> None:
        """Wipe any presence of a flow cell in cgstats"""
        from cg.apps.cgstats.crud.delete import delete_flowcell

        if self.dry_run:
            log.info(f"WipeDemuxAPI-CGStats: Would remove {self.flow_cell_name}")
        else:
            delete_flowcell(manager=self.stats_api, flowcell_name=self.flow_cell_name)

    def _wipe_demultiplexing_dir_hasta(self) -> None:
        """Wipe demultiplexing directory on server"""
        log.info(
            f"WipeDemuxAPI-Hasta: Removing flow cell demultiplexing directory: {self.demultiplexing_path}"
        )
        shutil.rmtree(self.demultiplexing_path, ignore_errors=False)

    def _wipe_run_dir_hasta(self) -> None:
        """Wipe flow cell run directory on server"""
        log.info(f"WipeDemuxAPI-Hasta: Removing flow cell run directory: {self.run_path}")
        shutil.rmtree(path=self.run_path, ignore_errors=False)

    def wipe_flow_cell_hasta(
        self,
        skip_demultiplexing_dir: bool,
        skip_run_dir: bool,
    ) -> None:
        """Wipe a flow cells presence on the server"""
        if self.dry_run:
            log.info(
                f"WipeDemuxAPI-Hasta: Would have removed the following directory: {self.demultiplexing_path}\n"
                f"WipeDemuxAPI-Hasta: Would have removed the following directory: {self.run_path}"
            )
        if not skip_demultiplexing_dir and self.demultiplexing_path.exists():
            self._wipe_demultiplexing_dir_hasta()
        else:
            log.info(
                f"WipeDemuxAPI-Hasta: Skipped demultiplexing directory, or no target: {self.demultiplexing_dir}"
            )
        if not skip_run_dir and self.run_path.exists():
            self._wipe_run_dir_hasta()
        else:
            log.info(
                f"WipeDemuxAPI-Hasta: Skipped flow cell run directory, or no target: {self.run_path}"
            )

    def wipe_demux_init_files(self):
        """Wipe previous traces of slurm job ids"""
        slurm_job_id_file_path: Path = self.run_path / "slurm_job_ids.yaml"
        demux_script_file_path: Path = self.run_path / "demux-novaseq.sh"
        try:
            error_log_path, log_path = glob(
                f"{self.run_path}/{self.flow_cell_name}_demultiplex.std*"
            )
            demux_init_files: List[Path] = [
                slurm_job_id_file_path,
                demux_script_file_path,
                Path(error_log_path),
                Path(log_path),
            ]
        except ValueError:
            log.info(f"No init demux logs found in: {self.run_path}")
            demux_init_files: List[Path] = [
                slurm_job_id_file_path,
                demux_script_file_path,
            ]
        for init_file in demux_init_files:
            if init_file.is_file():
                log.info(f"WipeDemuxAPI: Removing {init_file}")
                init_file.unlink()
            else:
                log.info(f"WipeDemuxAPI: Did not find {init_file}")

    def check_active_samples(self) -> None:
        """Check, and raise, if there are active samples on a flow cell"""
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

    def wipe_flow_cell(
        self,
        skip_cg_stats: bool,
        skip_demultiplexing_dir: bool,
        skip_run_dir: bool,
        skip_housekeeper: bool,
        skip_init_files: bool,
        skip_status_db: bool,
    ) -> None:
        """Master command to completely wipe the presence of a flowcell in all services"""
        self.check_active_samples()
        if not skip_demultiplexing_dir:
            self.wipe_flow_cell_hasta(
                skip_demultiplexing_dir=skip_demultiplexing_dir,
                skip_run_dir=skip_run_dir,
            )
        if not skip_cg_stats:
            self.wipe_flow_cell_cgstats()
        if not skip_init_files and skip_run_dir:
            self.wipe_demux_init_files()
        if not skip_housekeeper:
            self.wipe_flow_cell_housekeeper()
        if not skip_status_db:
            self.wipe_flow_cell_statusdb()

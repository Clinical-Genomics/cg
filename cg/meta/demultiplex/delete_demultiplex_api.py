import itertools
import logging
import shutil

from glob import glob
from pathlib import Path
from typing import Iterable, List, Optional

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.cgstats.stats import StatsAPI
from cg.constants import SequencingFileTag
from cg.exc import DeleteDemuxError
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Sample, Flowcell
from housekeeper.store.models import File

log = logging.getLogger(__name__)


class DeleteDemuxAPI:
    """Class to handle wiping out a flow cell before restart/start"""

    def __init__(self, config: CGConfig, demultiplex_base: Path, dry_run: bool, run_path: Path):
        self.dry_run: bool = self.set_dry_run(dry_run=dry_run)
        self.demultiplexing_dir: Path = demultiplex_base
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.run_path: Path = run_path
        self.status_db: Store = config.status_db
        self.stats_api: StatsAPI = config.cg_stats_api
        self.samples_on_flow_cell: List[Sample] = []
        log.debug("DeleteDemuxAPI: API initiated")

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
        log.debug(f"DeleteDemuxAPI: Setting dry run mode to {dry_run}")
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

    def _delete_sample_sheet_housekeeper(self) -> None:
        """Delete the presence of all sample sheets related to a flow cell in Housekeeper."""
        sample_sheet_files: Iterable[File] = self.housekeeper_api.files(
            tags=[self.flow_cell_name, "samplesheet"]
        )
        if any(sample_sheet_files):
            for file in sample_sheet_files:
                self.housekeeper_api.delete_file(file_id=file.id)
                log.info(f"DeleteDemuxAPI-Housekeeper: Deleted {file.path} from housekeeper")
        else:
            log.info(f"DeleteDemuxAPI-Housekeeper: No files found with tag: {self.flow_cell_name}")

    def _delete_files_if_related_in_housekeeper_by_tag(self, sample: Sample, tag: str):
        """Delete any existing fastq related to sample"""

        housekeeper_files: Iterable[File] = self.housekeeper_api.files(
            bundle=sample.internal_id, tags=[tag]
        )
        if not housekeeper_files:
            log.info(f"Could not find {tag} for {sample.internal_id}")
        else:
            for housekeeper_file in housekeeper_files:
                self.housekeeper_api.delete_file(file_id=housekeeper_file.id)

    def _delete_fastq_and_spring_housekeeper(self) -> None:
        """Delete the presence of any spring/fastq files in Housekeeper related to samples on the flow cell"""

        tags = [SequencingFileTag.FASTQ, SequencingFileTag.SPRING]
        for tag, sample in itertools.product(tags, self.samples_on_flow_cell):
            self._delete_files_if_related_in_housekeeper_by_tag(sample=sample, tag=tag)

    def delete_flow_cell_housekeeper(self) -> None:
        """Delete any presence of a flow cell in housekeeper. Including Sample sheets AND fastq-files"""

        if self.dry_run:
            log.info(
                f"DeleteDemuxAPI-Housekeeper: Would delete sample sheet files with tag {self.flow_cell_name}"
            )
            log.info(
                f"DeleteDemuxAPI-Housekeeper: Would delete fastq and spring files related to flow cell {self.flow_cell_name}"
            )
        else:
            log.info(
                f"DeleteDemuxAPI-Housekeeper: Deleting sample sheet files with tag {self.flow_cell_name}"
            )
            self._delete_sample_sheet_housekeeper()
            log.info(
                f"DeleteDemuxAPI-Housekeeper: Deleting fastq and spring files related to flowcell {self.flow_cell_name}"
            )
            self._delete_fastq_and_spring_housekeeper()

    def delete_flow_cell_statusdb(self) -> None:
        """Delete any presence of a flow cell in status-db"""
        if self.dry_run:
            log.info(f"DeleteDemuxAPI-StatusDB: Would remove {self.flow_cell_name}")
        else:
            self.status_db.delete_flow_cell(flow_cell_name=self.flow_cell_name)
            log.info(f"DeleteDemuxAPI-StatusDB: Deleted flowcell {self.flow_cell_name}")

    def delete_flow_cell_cgstats(self) -> None:
        """Delete any presence of a flow cell in cgstats"""
        from cg.apps.cgstats.crud.delete import delete_flowcell

        if self.dry_run:
            log.info(f"DeleteDemuxAPI-CGStats: Would remove {self.flow_cell_name}")
        else:
            delete_flowcell(manager=self.stats_api, flowcell_name=self.flow_cell_name)

    def _delete_demultiplexing_dir_hasta(self) -> None:
        """delete demultiplexing directory on server"""
        log.info(
            f"DeleteDemuxAPI-Hasta: Removing flow cell demultiplexing directory: {self.demultiplexing_path}"
        )
        shutil.rmtree(self.demultiplexing_path, ignore_errors=False)

    def _delete_run_dir_hasta(self) -> None:
        """delete flow cell run directory on server"""
        log.info(f"DeleteDemuxAPI-Hasta: Removing flow cell run directory: {self.run_path}")
        shutil.rmtree(path=self.run_path, ignore_errors=False)

    def delete_flow_cell_hasta(
        self,
        demultiplexing_dir: bool,
        run_dir: bool,
    ) -> None:
        """Delete a flow cells presence on the server, if flow cell is removed from demultiplexing dir and run
        dir set status to removed"""
        if self.dry_run:
            log.info(
                f"DeleteDemuxAPI-Hasta: Would have removed the following directory: {self.demultiplexing_path}\n"
                f"DeleteDemuxAPI-Hasta: Would have removed the following directory: {self.run_path}"
            )
            return
        if demultiplexing_dir and run_dir and self.status_db_presence:
            flow_cell_obj: Flowcell = self.status_db.get_flow_cell(self.flow_cell_name)
            flow_cell_obj.status = "removed"
            self.status_db.commit()
        if demultiplexing_dir and self.demultiplexing_path.exists():
            self._delete_demultiplexing_dir_hasta()
        else:
            log.info(
                f"DeleteDemuxAPI-Hasta: Skipped demultiplexing directory, or no target: {self.demultiplexing_dir}"
            )
        if run_dir and self.run_path.exists():
            self._delete_run_dir_hasta()
        else:
            log.info(
                f"DeleteDemuxAPI-Hasta: Skipped flow cell run directory, or no target: {self.run_path}"
            )

    def delete_demux_init_files(self):
        """Delete previous traces of slurm job ids"""
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
            log.info(f"DeleteDemuxAPI-Init-files: No demultiplexing logs found in: {self.run_path}")
            demux_init_files: List[Path] = [
                slurm_job_id_file_path,
                demux_script_file_path,
            ]
        if self.dry_run:
            log.info(f"DeleteDemuxAPI-Init-files: Would have removed {demux_init_files}")
        for init_file in demux_init_files:
            if init_file.is_file():
                log.info(f"DeleteDemuxAPI: Removing {init_file}")
                init_file.unlink()
            else:
                log.info(f"DeleteDemuxAPI: Did not find {init_file}")

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
                raise DeleteDemuxError

    def delete_flow_cell(
        self,
        cg_stats: bool,
        demultiplexing_dir: bool,
        run_dir: bool,
        housekeeper: bool,
        init_files: bool,
        status_db: bool,
    ) -> None:
        """Master command to delete the presence of a flowcell in all services"""
        self.check_active_samples()
        if status_db:
            self.delete_flow_cell_hasta(
                demultiplexing_dir=True,
                run_dir=True,
            )
            self.delete_flow_cell_cgstats()
            self.delete_flow_cell_housekeeper()
            self.delete_flow_cell_statusdb()
        if demultiplexing_dir or run_dir:
            self.delete_flow_cell_hasta(
                demultiplexing_dir=demultiplexing_dir,
                run_dir=run_dir,
            )
        if cg_stats:
            self.delete_flow_cell_cgstats()
        if init_files and not run_dir:
            self.delete_demux_init_files()
        if housekeeper:
            self.delete_flow_cell_housekeeper()

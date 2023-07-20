import itertools
import logging
import shutil

from glob import glob
from pathlib import Path
from typing import Iterable, List, Optional
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.cgstats.stats import StatsAPI
from cg.constants import SequencingFileTag
from cg.exc import DeleteDemuxError
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Sample, Flowcell
from housekeeper.store.models import File

LOG = logging.getLogger(__name__)


class DeleteDemuxAPI:
    """Class to handle wiping out a flow cell before restart/start"""

    def __init__(self, config: CGConfig, dry_run: bool, flow_cell_name: str):
        self.dry_run: bool = self.set_dry_run(dry_run=dry_run)
        self.flow_cell_name = flow_cell_name
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.status_db: Store = config.status_db
        self.demux_api: DemultiplexingAPI = config.demultiplex_api
        self.stats_api: StatsAPI = config.cg_stats_api
        self.samples_on_flow_cell: List[Sample] = []
        self.demultiplexing_out_path: Path = self.get_path_for_flow_cell(
            base_path=self.demux_api.out_dir
        )
        self.run_path: Path = self.get_path_for_flow_cell(base_path=self.demux_api.run_dir)
        LOG.debug("DeleteDemuxAPI: API initiated")

    def get_path_for_flow_cell(
        self,
        base_path: Path,
    ) -> Path:
        """
        Return the path to the run dir or demultiplex dir for the given flow cell name
        depending on the base_path input.
        """
        flow_cell_path = next(base_path.rglob(pattern=f"*{self.flow_cell_name}"), None)
        if flow_cell_path and flow_cell_path.exists():
            return flow_cell_path
        else:
            LOG.warning(
                f"DeleteDemuxAPI: Path {flow_cell_path} not found for {self.flow_cell_name}"
            )

    @property
    def status_db_presence(self) -> bool:
        """Update about the presence of given flow cell in status_db"""
        return bool(self.status_db.get_flow_cell_by_name(flow_cell_name=self.flow_cell_name))

    @staticmethod
    def set_dry_run(dry_run: bool) -> bool:
        """Set dry run flag for API"""
        LOG.debug(f"DeleteDemuxAPI: Setting dry run mode to {dry_run}")
        return dry_run

    def _set_samples_on_flow_cell(self) -> None:
        """Set a list of samples related to a flow cell in status-db."""
        flow_cell = self.status_db.get_flow_cell_by_name(flow_cell_name=self.flow_cell_name)
        self.samples_on_flow_cell: List[Sample] = flow_cell.samples

    def active_samples_on_flow_cell(self) -> Optional[List[str]]:
        """Check if there are any active cases related to samples of a flow cell."""
        active_samples_on_flow_cell: List[str] = [
            sample.internal_id
            for sample in self.samples_on_flow_cell
            if self.status_db.has_active_cases_for_sample(internal_id=sample.internal_id)
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
                LOG.info(f"DeleteDemuxAPI-Housekeeper: Deleted {file.path} from housekeeper")
        else:
            LOG.info(f"DeleteDemuxAPI-Housekeeper: No files found with tag: {self.flow_cell_name}")

    def _delete_files_if_related_in_housekeeper_by_tag(self, sample: Sample, tags: List[str]):
        """Delete any existing fastq related to sample"""

        housekeeper_files: Iterable[File] = self.housekeeper_api.files(
            bundle=sample.internal_id, tags=tags
        )
        if not housekeeper_files:
            LOG.info(f"Could not find {tags} for {sample.internal_id}")
        else:
            for housekeeper_file in housekeeper_files:
                self.housekeeper_api.delete_file(file_id=housekeeper_file.id)

    def _delete_fastq_and_spring_housekeeper(self) -> None:
        """Delete the presence of any spring/fastq files in Housekeeper related to samples on the flow cell."""

        tag_combinations: List[List[str]] = [
            [SequencingFileTag.FASTQ.value, self.flow_cell_name],
            [SequencingFileTag.SPRING.value, self.flow_cell_name],
            [SequencingFileTag.SPRING_METADATA.value, self.flow_cell_name],
        ]
        for tags, sample in itertools.product(tag_combinations, self.samples_on_flow_cell):
            self._delete_files_if_related_in_housekeeper_by_tag(sample=sample, tags=tags)

    def delete_flow_cell_housekeeper(self) -> None:
        """Delete any presence of a flow cell in housekeeper. Including Sample sheets AND fastq-files"""

        if self.dry_run:
            LOG.info(
                f"DeleteDemuxAPI-Housekeeper: Would delete sample sheet files with tag {self.flow_cell_name}"
            )
            LOG.info(
                f"DeleteDemuxAPI-Housekeeper: Would delete fastq and spring files related to flow cell {self.flow_cell_name}"
            )
        else:
            LOG.info(
                f"DeleteDemuxAPI-Housekeeper: Deleting sample sheet files with tag {self.flow_cell_name}"
            )
            self._delete_sample_sheet_housekeeper()
            LOG.info(
                f"DeleteDemuxAPI-Housekeeper: Deleting fastq and spring files related to flowcell {self.flow_cell_name}"
            )
            self._delete_fastq_and_spring_housekeeper()

    def delete_flow_cell_in_status_db(self) -> None:
        """Delete a flow cell in Status db."""
        if self.dry_run:
            LOG.info(f"DeleteDemuxAPI-StatusDB: Would remove {self.flow_cell_name}")
        else:
            self.status_db.delete_flow_cell(flow_cell_id=self.flow_cell_name)
            LOG.info(f"DeleteDemuxAPI-StatusDB: Deleted flowcell {self.flow_cell_name}")

    def delete_flow_cell_cgstats(self) -> None:
        """Delete any presence of a flow cell in cgstats"""
        from cg.apps.cgstats.crud.delete import delete_flowcell

        if self.dry_run:
            LOG.info(f"DeleteDemuxAPI-CGStats: Would remove {self.flow_cell_name}")
        else:
            delete_flowcell(manager=self.stats_api, flowcell_name=self.flow_cell_name)

    def delete_flow_cell_sample_lane_sequencing_metrics(self) -> None:
        if self.dry_run:
            LOG.info(
                f"Would delete entries for Flow Cell: {self.flow_cell_name} in the Sample Lane Sequencing Metrics table"
            )
        else:
            LOG.info(
                f"Delete entries for Flow Cell: {self.flow_cell_name} in the Sample Lane Sequencing Metrics table"
            )
            self.status_db.delete_flow_cell_entries_in_sample_lane_sequencing_metrics(
                flow_cell_name=self.flow_cell_name
            )

    def _delete_demultiplexing_dir_hasta(self, demultiplexing_dir: bool) -> None:
        """delete demultiplexing directory on server."""
        if demultiplexing_dir and self.demultiplexing_out_path.exists():
            LOG.info(
                f"DeleteDemuxAPI-Hasta: Removing flow cell demultiplexing directory: {self.demultiplexing_out_path}"
            )
            shutil.rmtree(self.demultiplexing_out_path, ignore_errors=False)
        else:
            LOG.info(
                f"DeleteDemuxAPI-Hasta: No demultiplexing directory found for {self.flow_cell_name}"
            )

    def _delete_run_dir_hasta(self, run_dir: bool) -> None:
        """delete flow cell run directory on server."""
        if run_dir and self.run_path.exists():
            LOG.info(f"DeleteDemuxAPI-Hasta: Removing flow cell run directory: {self.run_path}")
            shutil.rmtree(path=self.run_path, ignore_errors=False)
        else:
            LOG.info(f"DeleteDemuxAPI-Hasta: No run directory found for {self.flow_cell_name}")

    def delete_flow_cell_hasta(
        self,
        demultiplexing_dir: bool,
        run_dir: bool,
    ) -> None:
        """Delete a flow cells presence on the server, if flow cell is removed from demultiplexing dir and run
        dir set status to removed."""
        if self.dry_run:
            LOG.info(
                f"DeleteDemuxAPI-Hasta: Would have removed the following directory: {self.demultiplexing_out_path}\n"
                f"DeleteDemuxAPI-Hasta: Would have removed the following directory: {self.run_path}"
            )
            return
        self.set_flow_cell_status_statusdb_to_removed(
            demultiplexing_dir=demultiplexing_dir,
            run_dir=run_dir,
            status_db=self.status_db_presence,
        )
        self._delete_demultiplexing_dir_hasta(demultiplexing_dir=demultiplexing_dir)
        self._delete_run_dir_hasta(run_dir=run_dir)

    def set_flow_cell_status_statusdb_to_removed(
        self, demultiplexing_dir: bool, run_dir: bool, status_db: bool
    ) -> None:
        if demultiplexing_dir and run_dir and status_db:
            flow_cell_obj: Flowcell = self.status_db.get_flow_cell_by_name(
                flow_cell_name=self.flow_cell_name
            )
            flow_cell_obj.status = "removed"
            self.status_db.session.commit()

    def delete_demux_init_files(self):
        """Delete previous traces of slurm job ids."""
        slurm_job_id_file_path: Path = Path(self.run_path, "slurm_job_ids.yaml")
        demux_script_file_path: Path = Path(self.run_path, "demux-novaseq.sh")
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
            LOG.info(f"DeleteDemuxAPI-Init-files: No demultiplexing logs found in: {self.run_path}")
            demux_init_files: List[Path] = [
                slurm_job_id_file_path,
                demux_script_file_path,
            ]
        if self.dry_run:
            LOG.info(f"DeleteDemuxAPI-Init-files: Would have removed {demux_init_files}")
        for init_file in demux_init_files:
            if init_file.is_file():
                LOG.info(f"DeleteDemuxAPI: Removing {init_file}")
                init_file.unlink()
            else:
                LOG.info(f"DeleteDemuxAPI: Did not find {init_file}")

    def check_active_samples(self) -> None:
        """Check, and raise, if there are active samples on a flow cell."""
        if self.status_db_presence:
            self._set_samples_on_flow_cell()
            active_samples_on_flow_cell: List[str] = self.active_samples_on_flow_cell()
            if active_samples_on_flow_cell:
                LOG.warning(
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
        sample_lane_sequencing_metrics: bool,
        init_files: bool,
        status_db: bool,
    ) -> None:
        """Master command to delete the presence of a flow cell in all services."""
        self.check_active_samples()
        if status_db:
            self.delete_flow_cell_hasta(
                demultiplexing_dir=True,
                run_dir=True,
            )
            self.delete_flow_cell_cgstats()
            self.delete_flow_cell_housekeeper()
            self.delete_flow_cell_in_status_db()

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
        if sample_lane_sequencing_metrics:
            self.delete_flow_cell_sample_lane_sequencing_metrics()

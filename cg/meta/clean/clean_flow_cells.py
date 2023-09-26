"""An API that handles the cleaning of flow cells on Hasta."""
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.store import Store
from cg.store.models import Flowcell, SampleLaneSequencingMetrics
from cg.utils.date import get_timedelta_from_date
from cg.utils.files import get_creation_date, remove_directory_and_contents


class CleanFlowCellsAPI:
    """
            Handles the cleaning of flow cells in the flow_cells and demultiplexed_runs directories.
    Requirements for cleaning:
            Flow cell is older than 21 days
            Flow cells are backed up on PDC get from statusDB
            Flow cell is in statusDB
            Flow cell has sequencing metrics in statusDB
            Flow cell has fastq files in housekeeper
            Flow cell has SPRING files in housekeeper
            Flow cell has a sample sheet in housekeeper
    """

    def __init__(self, config: CGConfig, flow_cell_path: Path):
        self.config: CGConfig = config
        self.status_db: Store = config.status_db
        self.hk_api: HousekeeperAPI = config.housekeeper_api
        self.flow_cell = FlowCellDirectoryData(flow_cell_path=flow_cell_path)

    def delete_flow_cell_directory(self):
        """Delete the flow cell directory if it fulfills all requirements."""
        if self.can_flow_cell_directory_be_deleted():
            remove_directory_and_contents(self.flow_cell.path)

    def can_flow_cell_directory_be_deleted(self) -> bool:
        """Determine whether a flow cell directory can be deleted."""
        return all(
            [
                self.is_directory_older_than_days_old(),
                self.is_flow_cell_in_statusdb(),
                self.is_flow_cell_backed_up(),
                self.has_sequencing_metrics(),
                self.has_fastq_files_in_housekeeper(),
                self.has_spring_files_in_housekeeper(),
                self.has_sample_sheet_in_housekeeper(),
            ]
        )

    def is_directory_older_than_days_old(self, days_old: int = 21) -> bool:
        """Check if a given directory is older than specified number of days."""
        dir_creation_date: datetime = get_creation_date(self.flow_cell.path)
        time_delta: timedelta = get_timedelta_from_date(dir_creation_date)
        return bool(time_delta.days > days_old)

    def get_flow_cell_from_status_db(self) -> Flowcell:
        """Get the flow cell entry from statusDB.
        Raises:
              ValueError if the flow cell is not found in statusDB
        """
        flow_cell: Flowcell = self.status_db.get_flow_cell_by_name(self.flow_cell.id)
        if not flow_cell:
            raise ValueError(f"Flow cell {flow_cell.id} not found in statusDB.")
        return flow_cell

    def is_flow_cell_in_statusdb(self) -> bool:
        """Check if flow cell is in statusdb."""
        return bool(self.get_flow_cell_from_status_db())

    def is_flow_cell_backed_up(self) -> bool:
        """Check if flow cell is backed up on PDC."""
        return bool(self.get_flow_cell_from_status_db().has_backup)

    def get_sequencing_metrics_for_flow_cell(self):
        """Get the SampleLaneSequencingMetrics entries for a flow cell."""
        metrics: List[
            SampleLaneSequencingMetrics
        ] = self.status_db.get_sample_lane_sequencing_metrics_by_flow_cell_name(self.flow_cell.id)
        if not metrics:
            raise ValueError(
                f"No SampleLaneSequencingMetrics found for flow cell {self.flow_cell.id} in statusDB"
            )
        return metrics

    def has_sequencing_metrics(self):
        """Check if a flow cell has entries in the SampleLaneSequencingMetrics table."""
        return bool(self.get_sequencing_metrics_for_flow_cell())

    def has_sample_sheet_in_housekeeper(self) -> bool:
        """Check if the flow cell has a sample sheet in housekeeper."""
        return bool(self.flow_cell.get_sample_sheet_path_hk())

    def get_files_for_flow_cell_bundle(self, tag: str):
        """Get the files with a specific tag from housekeeper for the flow cell bundle."""
        files: List[File] = self.hk_api.get_files_from_latest_version(
            bundle_name=self.flow_cell.id, tags=[tag]
        )
        if not files:
            raise ValueError(
                f"No files with tag {tag} found for flow cell bundle {self.flow_cell.id}"
            )
        return files

    def has_fastq_files_in_housekeeper(self) -> bool:
        """Check if the flow cell has fastq files in housekeeper."""
        return bool(self.get_files_for_flow_cell_bundle(tag=SequencingFileTag.FASTQ))

    def has_spring_files_in_housekeeper(self) -> bool:
        """Check if the flow cell has SPRING files in housekeeper."""
        return bool(self.get_files_for_flow_cell_bundle(tag=SequencingFileTag.SPRING))

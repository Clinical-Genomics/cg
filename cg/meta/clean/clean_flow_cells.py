"""An API that handles the cleaning of flow cells on Hasta."""
import logging
import time
from pathlib import Path
from typing import List

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.time import TWENTY_ONE_DAYS_IN_SECONDS
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.store import Store
from cg.store.models import Flowcell, SampleLaneSequencingMetrics
from cg.utils.files import get_creation_time_stamp, remove_directory_and_contents

LOG = logging.getLogger(__name__)


class CleanFlowCellAPI:
    """
            Handles the cleaning of flow cells in the flow_cells and demultiplexed_runs directories.
    Requirements for cleaning:
            Flow cell is older than 21 days
            Flow cell is backed up
            Flow cell is in StatusDB
            Flow cell has sequencing metrics in StatusDB
            Flow cell has fastq files in Housekeeper
            Flow cell has SPRING files in Housekeeper
            Flow cell has a sample sheet in Housekeeper
    """

    def __init__(
        self, status_db: Store, housekeeper_api: HousekeeperAPI, flow_cell_path: Path, dry_run: bool
    ):
        self.status_db: Store = status_db
        self.hk_api: HousekeeperAPI = housekeeper_api
        self.flow_cell = FlowCellDirectoryData(flow_cell_path=flow_cell_path)
        self.current_time = time.time()
        self.dry_run: bool = dry_run

    def delete_flow_cell_directory(self):
        """Delete the flow cell directory if it fulfills all requirements."""
        is_error_raised: bool = False
        try:
            if self.can_flow_cell_directory_be_deleted():
                if self.dry_run:
                    LOG.debug(f"Dry run: Would have removed: {self.flow_cell.path}")
                    return
                remove_directory_and_contents(self.flow_cell.path)
                return is_error_raised
        except Exception as error:
            is_error_raised = True
            LOG.error(f"Flow cell with path {self.flow_cell.path} not removed: {str(error)}")
            return is_error_raised

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

    def is_directory_older_than_days_old(self) -> bool:
        """Check if a given directory is older than specified number of days.
        The check is performed by comparing whether the directory creation time stamp in seconds
        is greater than the current time minus 21 days in seconds.
        """
        dir_creation_time_stamp: float = get_creation_time_stamp(self.flow_cell.path)

        return bool(dir_creation_time_stamp < self.current_time - TWENTY_ONE_DAYS_IN_SECONDS)

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
        """Get the SampleLaneSequencingMetrics entries for a flow cell.
        Raises:
            ValueError if no SampleLaneSequencingMetrics entry is found."""
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
        """Get the files with a specific tag from Housekeeper for the flow cell bundle."""
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

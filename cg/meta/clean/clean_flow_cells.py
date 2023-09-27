"""An API that handles the cleaning of flow cells."""
import logging
import time
from pathlib import Path
from typing import List, Optional

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.time import TWENTY_ONE_DAYS
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.store import Store
from cg.store.models import Flowcell, SampleLaneSequencingMetrics
from cg.utils.files import remove_directory_and_contents
from cg.utils.time import is_directory_older_than_days_old

LOG = logging.getLogger(__name__)


class CleanFlowCellAPI:
    """
            Handles the cleaning of flow cells in the flow cells and demultiplexed runs directories.
    Requirements for cleaning:
            Flow cell is older than 21 days
            Flow cell is backed up
            Flow cell is in StatusDB
            Flow cell has sequencing metrics in StatusDB
            Flow cell has fastq files in Housekeeper
            Flow cell has SPRING files in Housekeeper
            Flow cell has SPRING metadata in Housekeeper
            Flow cell has a sample sheet in Housekeeper
    """

    def __init__(
        self, status_db: Store, housekeeper_api: HousekeeperAPI, flow_cell_path: Path, dry_run: bool
    ):
        self.status_db: Store = status_db
        self.hk_api: HousekeeperAPI = housekeeper_api
        self.flow_cell = FlowCellDirectoryData(flow_cell_path=flow_cell_path)
        self.current_time: float = time.time()
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
                self.is_directory_older_than_21_days(),
                self.is_flow_cell_in_statusdb(),
                self.is_flow_cell_backed_up(),
                self.has_sequencing_metrics(),
                self.has_fastq_files_in_housekeeper(),
                self.has_spring_meta_data_files_in_housekeeper(),
                self.has_spring_files_in_housekeeper(),
                self.has_sample_sheet_in_housekeeper(),
            ]
        )

    def is_directory_older_than_21_days(self) -> bool:
        """Check if a given directory is older than 21 days."""
        return is_directory_older_than_days_old(
            directory_path=self.flow_cell.path,
            days_old=TWENTY_ONE_DAYS,
            current_time=self.current_time,
        )

    def get_flow_cell_from_status_db(self) -> Optional[Flowcell]:
        """Get the flow cell entry from StatusDB."""
        flow_cell: Flowcell = self.status_db.get_flow_cell_by_name(self.flow_cell.id)
        if not flow_cell:
            LOG.warning(f"Flow cell {self.flow_cell.id} not found in StatusDB.")
        return flow_cell

    def is_flow_cell_in_statusdb(self) -> bool:
        """Check if flow cell is in statusdb."""
        return bool(self.get_flow_cell_from_status_db())

    def is_flow_cell_backed_up(self) -> bool:
        """Check if flow cell is backed up on PDC."""
        return bool(self.get_flow_cell_from_status_db().has_backup)

    def get_sequencing_metrics_for_flow_cell(self) -> Optional[List[SampleLaneSequencingMetrics]]:
        """Get the SampleLaneSequencingMetrics entries for a flow cell."""
        metrics: List[
            SampleLaneSequencingMetrics
        ] = self.status_db.get_sample_lane_sequencing_metrics_by_flow_cell_name(self.flow_cell.id)
        if not metrics:
            LOG.warning(
                f"No SampleLaneSequencingMetrics found for flow cell {self.flow_cell.id} in StatusDB"
            )
        return metrics

    def has_sequencing_metrics(self) -> bool:
        """Check if a flow cell has entries in the SampleLaneSequencingMetrics table."""
        return bool(self.get_sequencing_metrics_for_flow_cell())

    def has_sample_sheet_in_housekeeper(self) -> bool:
        """Check if the flow cell has a sample sheet in housekeeper."""
        return bool(self.flow_cell.get_sample_sheet_path_hk())

    def has_files_for_samples_on_flow_cell_with_tag(self, tag: str) -> bool:
        """
        Get the files with a specified tag from Housekeeper for the samples on a flow cell.
        """
        flow_cell: Flowcell = self.get_flow_cell_from_status_db()
        bundle_names: List[str] = [sample.internal_id for sample in flow_cell.samples]
        all_samples_have_files: bool = True
        for bundle_name in bundle_names:
            files: List[File] = self.hk_api.get_files_from_latest_version(
                bundle_name=bundle_name, tags=[tag, self.flow_cell.id]
            ).all()
            if not files:
                LOG.warning(f"No files with tag {tag}  found in bundle {bundle_name}.")
                all_samples_have_files = False
        return all_samples_have_files

    def has_fastq_files_in_housekeeper(self) -> bool:
        """Check if all samples on the flow cell have fastq files in housekeeper."""
        return self.has_files_for_samples_on_flow_cell_with_tag(tag=SequencingFileTag.FASTQ)

    def has_spring_files_in_housekeeper(self) -> bool:
        """Check if all samples on the flow cell have SPRING files in housekeeper."""
        return self.has_files_for_samples_on_flow_cell_with_tag(tag=SequencingFileTag.SPRING)

    def has_spring_meta_data_files_in_housekeeper(self) -> bool:
        """Check if all samples on the flow cell have SPRING metadata files in housekeeper."""
        return self.has_files_for_samples_on_flow_cell_with_tag(
            tag=SequencingFileTag.SPRING_METADATA
        )

"""Module that handles deletion of flow cell run directories and their BCL files from
flow_cell_run_dir/<sequencer>."""
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FlowCellStatus
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.constants.symbols import UNDERSCORE
from cg.store import Store
from cg.store.models import Flowcell
from cg.utils.date import get_timedelta_from_date
from housekeeper.store.models import Bundle, File

FLOW_CELL_DATE_POSITION = 0
FLOW_CELL_IDENTIFIER_POSITION = -1
LOG = logging.getLogger(__name__)
PDC_RETRIEVAL_STATUSES = [FlowCellStatus.PROCESSING, FlowCellStatus.RETRIEVED]


class RunDirFlowCell:
    """Class to check and remove flow cell run directories."""

    def __init__(self, flow_cell_dir: Path, status_db: Store, housekeeper_api: HousekeeperAPI):
        self.flow_cell_dir: Path = flow_cell_dir
        self.status_db: Store = status_db
        self.hk: HousekeeperAPI = housekeeper_api
        self.flow_cell_name: str = self.flow_cell_dir.name
        self.identifier: str = self.flow_cell_name.split(UNDERSCORE)[FLOW_CELL_IDENTIFIER_POSITION]
        self.run_date: str = self.flow_cell_name.split(UNDERSCORE)[FLOW_CELL_DATE_POSITION]
        self.derived_date: datetime = datetime.strptime(self.run_date, "%y%m%d")
        self.id: str = self.identifier[1:]
        self._age: Optional[timedelta] = None
        self._is_retrieved_from_pdc: Optional[bool] = None
        self._exists_in_statusdb: Optional[bool] = None
        self._sequenced_date: Optional[datetime] = None
        self._flow_cell_status: Optional[str] = None
        self.sample_sheet_path: Path = (
            self.flow_cell_dir / DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
        )

    @property
    def age(self) -> int:
        """How long ago a flow cell was sequenced, in days."""
        if self._age is None:
            self._age: int = (get_timedelta_from_date(date=self.sequenced_date)).days
        return self._age

    @property
    def sequenced_date(self) -> datetime:
        """The date on which the flow cell was sequenced."""
        if self._sequenced_date is None:
            flow_cell: Flowcell = self.status_db.get_flow_cell_by_name(flow_cell_name=self.id)
            if flow_cell:
                LOG.info(f"Found flow cell {self.id} in Statusdb, getting sequenced date.")
                self._sequenced_date: datetime = flow_cell.sequenced_at
            else:
                LOG.info(
                    f"Flow cell {self.id} NOT found in Statusdb, deriving sequenced date from run dir name!"
                )
                self._sequenced_date: datetime = self.derived_date
        return self._sequenced_date

    @property
    def is_retrieved_from_pdc(self) -> bool:
        """Flow cell is (being) retrieved from PDC."""
        if self._is_retrieved_from_pdc is None:
            self._is_retrieved_from_pdc = self.flow_cell_status in PDC_RETRIEVAL_STATUSES
        return self._is_retrieved_from_pdc

    @property
    def flow_cell_status(self) -> str:
        """Return status of the flow cell."""
        if self._flow_cell_status is None:
            self._flow_cell_status = self.status_db.get_flow_cell_by_name(
                flow_cell_name=self.id
            ).status
        return self._flow_cell_status

    @property
    def exists_in_statusdb(self) -> bool:
        """The flow cell exists in Statusdb."""
        if self._exists_in_statusdb is None:
            self._exists_in_statusdb = (
                self.status_db.get_flow_cell_by_name(flow_cell_name=self.id) is not None
            )
        return self._exists_in_statusdb

    def remove_run_directory(self) -> None:
        """Removes the flow cell run directory."""
        LOG.info(f"Removing run directory {self.flow_cell_dir}")
        shutil.rmtree(self.flow_cell_dir, ignore_errors=True)

    def archive_sample_sheet(self) -> None:
        """Archives a sample sheet in Housekeeper bundles."""
        LOG.info(f"Start archiving sample sheet {self.sample_sheet_path}")
        if not self.sample_sheet_path.exists():
            LOG.warning("Sample sheet does not exists!")
            return
        LOG.info("Sample sheet found!")
        hk_bundle: Bundle = self.hk.bundle(name=self.id)
        if hk_bundle is None:
            LOG.info(f"Creating bundle with name {self.id}")
            hk_bundle = self.hk.create_new_bundle_and_version(name=self.id)
        sample_sheets_from_latest_version: List[File] = self.get_sample_sheets_from_latest_version(
            hk_bundle_name=hk_bundle.name
        )
        for file in sample_sheets_from_latest_version:
            if file.is_included:
                LOG.warning("Sample sheet already included!")
                return
        hk_tags = [self.id, SequencingFileTag.SAMPLE_SHEET]
        self.hk.add_and_include_file_to_latest_version(
            bundle_name=self.id,
            file=self.sample_sheet_path,
            tags=hk_tags,
        )

    def get_sample_sheets_from_latest_version(self, hk_bundle_name: str) -> List[File]:
        """Returns the files tagged with samplesheet or archived_sample_sheet for the given bundle."""
        files: List[File] = self.hk.get_files_from_latest_version(
            bundle_name=hk_bundle_name, tags=[self.id]
        ).all()
        return self.filter_on_sample_sheets(files=files)

    @staticmethod
    def filter_on_sample_sheets(files: List[File]) -> List[File]:
        """Filters the given list of Files to return only those tagged with samplesheet or archived_sample_sheet."""
        files_with_a_sample_sheet_tag: List[File] = []
        for file in files:
            file_tag_names: List[str] = [tag.name for tag in file.tags]
            if (
                SequencingFileTag.SAMPLE_SHEET in file_tag_names
                or SequencingFileTag.ARCHIVED_SAMPLE_SHEET in file_tag_names
            ):
                files_with_a_sample_sheet_tag.append(file)
        return [*set(files_with_a_sample_sheet_tag)]

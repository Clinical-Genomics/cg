"""Module that handles deletion of flow cell run directories and their BCL files from
flow_cell_run_dir/<sequencer> """
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from housekeeper.store import models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import HousekeeperTags
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.symbols import UNDERSCORE
from cg.store import Store

FLOW_CELL_DATE_POSITION = 0
FLOW_CELL_IDENTIFIER_POSITION = 3
LOG = logging.getLogger(__name__)


class RunDirFlowCell:
    """Class to check and remove flow cell run directories. If a flow cell has been sequenced 21
    days ago or more, it is removed and the sample sheet is archived"""

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
        self._sequenced_date: Optional[datetime] = None
        self.sample_sheet_path: Path = (
            self.flow_cell_dir / DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
        )

    @property
    def age(self) -> int:
        """How long ago a flow cell was sequenced, in days"""
        if self._age is None:
            LOG.info("Setting age property")
            self._age = (datetime.now() - self.sequenced_date).days
        return self._age

    @property
    def sequenced_date(self) -> datetime:
        """The date on which the flow cell was sequenced"""
        if self._sequenced_date is None:
            LOG.info("Setting sequenced date property")
            if self.status_db.flowcell(name=self.id):
                LOG.info("Found flow cell %s in statusdb, getting sequenced date.", self.id)
                self._sequenced_date = self.status_db.flowcell(name=self.id).sequenced_at
            else:
                LOG.info(
                    "Flow cell %s NOT found in statusdb, deriving sequenced date from run dir name!",
                    self.id,
                )
                self._sequenced_date = self.derived_date
        return self._sequenced_date

    def remove_run_directory(self):
        """Removes the flow cell run directory"""
        LOG.info("Removing run directory %s", self.flow_cell_dir)
        shutil.rmtree(self.flow_cell_dir, ignore_errors=True)

    def archive_sample_sheet(self):
        """Archives a sample sheet in housekeeper-bundles"""
        LOG.info("Start archiving sample sheet %s", self.sample_sheet_path)
        if not self.sample_sheet_path.exists():
            LOG.warning("Sample sheet does not exists!")
            return
        LOG.info("Sample sheet found!")
        hk_bundle: hk_models.Bundle = self.hk.bundle(name=self.id)
        if hk_bundle is None:
            LOG.info("Creating bundle with name %s", self.id)
            hk_bundle = self.hk.create_new_bundle_and_version(name=self.id)

        with self.hk.session_no_autoflush():
            hk_version: hk_models.Version = self.hk.last_version(bundle=hk_bundle.name)
            if self.hk.files(path=str(self.sample_sheet_path)).first() is None:
                LOG.info(f"Adding sample sheet to Housekeeper")
                tags: List[str] = [HousekeeperTags.ARCHIVED_SAMPLE_SHEET, self.id]
                self.hk.add_file(
                    path=str(self.sample_sheet_path), version_obj=hk_version, tags=tags
                )
        self.hk.commit()

        hk_sample_sheet_file: hk_models.File = self.hk.get_files(
            bundle=self.id, tags=[HousekeeperTags.ARCHIVED_SAMPLE_SHEET]
        ).first()

        if hk_sample_sheet_file.is_included:
            LOG.info("Sample sheet already included!")
            return
        LOG.info("Including sample sheet")
        self.hk.include_file(file_obj=hk_sample_sheet_file, version_obj=hk_version)
        self.hk.commit()

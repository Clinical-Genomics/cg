"""Module that handles deletion of flow cell run directories and their BCL files from
/home/proj/production/flowcells/<sequencer> """
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from cg.constants.symbols import UNDERSCORE
from cg.store import Store

FLOW_CELL_DATE_POSITION = 0
FLOW_CELL_IDENTIFIER_POSITION = 3
LOG = logging.getLogger(__name__)


class RunDirFlowCell:
    """Class to check and remove flow cell run directories. If a flow cell has been sequenced 21
    days ago or more, it is removed and the sample sheet is archived"""

    def __init__(self, status_db: Store, flow_cell_dir: Path):
        self.status_db = status_db
        self.flow_cell_dir: Path = flow_cell_dir
        self.flow_cell_name: str = self.flow_cell_dir.name
        self.identifier: str = self.flow_cell_name.split(UNDERSCORE)[FLOW_CELL_IDENTIFIER_POSITION]
        self.derived_date: str = self.flow_cell_name.split(UNDERSCORE)[FLOW_CELL_DATE_POSITION]
        self.id: str = self.identifier[1:]
        self._age: Optional[timedelta] = None
        self._sequenced_date: Optional[datetime] = None

    @property
    def age(self) -> int:
        """Determines how long ago a flow cell was sequenced, in days"""
        if self._age is None:
            self._age = (datetime.now() - self.sequenced_date).days
        return self._age

    @property
    def sequenced_date(self) -> datetime:
        """The date on which the flow cell was sequenced"""
        if self._sequenced_date is None:
            if self.status_db.flowcell(name=self.id):
                LOG.debug("Found flow cell %s in statusdb", self.id)
                self._sequenced_date = self.status_db.flowcell(name=self.id).sequenced_at
            else:
                LOG.debug(
                    "Flow cell %s NOT found in statusdb, deriving sequenced date from run dir name!",
                    self.id,
                )
                self._sequenced_date = datetime.strptime(self.derived_date, "%y%m%d")

        return self._sequenced_date

    def remove_run_directory(self):
        """Removes the flow cell run directory"""
        shutil.rmtree(self.flow_cell_dir, ignore_errors=True)

        pass

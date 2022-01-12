"""Module that handles data and information regarding flow cells and flow cell directories. Used to
inspect and clean flow cell directories in demultiplexed runs """
import logging
import re
import shutil
from pathlib import Path
from typing import List, Optional

from alchy import Query

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FlowCellStatus, HousekeeperTags
from cg.store import Store

FLOW_CELL_IDENTIFIER_POSITION = 3
LOG = logging.getLogger(__name__)


class DemultiplexedRunsFlowCell:
    """Class to check if a given flow cell in demultiplexed-runs is valid, or can be removed. A
    valid flow cell is named correctly, has the correct status ('ondisk') in statusdb,
    and has fastq files in Housekeeper.

    A flow cell that is correctly named has four segments divided by underscores:
    <run_date>_<sequencer>_<run_number>_<identifier>. The identifier consists of the position of
    the flow cell on the sequencer in the first position (either A or B), and the flow cell id in
    the rest of the identifier. Flow cell id is the naming convention used in statusdb and other
    systems"""

    def __init__(
        self,
        flow_cell_path: Path,
        status_db: Store,
        housekeeper_api: HousekeeperAPI,
        fastq_files: Optional[Query] = None,
        spring_files: Optional[Query] = None,
    ):
        self.path: Path = flow_cell_path
        self.status_db: Store = status_db
        self.hk: HousekeeperAPI = housekeeper_api
        self.all_fastq_files: Optional[Query] = fastq_files
        self.all_spring_files: Optional[Query] = spring_files
        self.run_name: str = self.path.name
        self.split_name: List[str] = re.split("[_.]", self.run_name)
        self.identifier: str = self.split_name[FLOW_CELL_IDENTIFIER_POSITION]
        self.id: str = self.identifier[1:]
        self._hk_fastq_files = None
        self._hk_spring_files = None
        self._is_correctly_named = None
        self._exists_in_statusdb = None
        self._fastq_files_exist_in_housekeeper = None
        self._spring_files_exist_in_housekeeper = None
        self._files_exist_in_housekeeper = None
        self._files_exist_on_disk = None
        self._passed_check = None

    @property
    def hk_fastq_files(self) -> list:
        """All fastq files in Housekeeper for a particular flow cell"""
        if self._hk_fastq_files is None:
            self._hk_fastq_files = [
                fastq_file for fastq_file in self.all_fastq_files if self.id in fastq_file.path
            ]
        return self._hk_fastq_files

    @property
    def hk_spring_files(self) -> list:
        """All spring files in Housekeeper for a particular flow cell"""
        if self._hk_spring_files is None:
            self._hk_spring_files = [
                spring_file for spring_file in self.all_spring_files if self.id in spring_file.path
            ]
        return self._hk_spring_files

    @property
    def is_correctly_named(self) -> bool:
        """Checks if the flow cell directory is correctly named: it should end with the flow cell
        id"""
        if self._is_correctly_named is None:
            self._is_correctly_named: bool = self.split_name[-1] == self.identifier
            if not self._is_correctly_named:
                LOG.warning("Flow cell name not correctly named!: %s", self.path)
        return self._is_correctly_named

    @property
    def exists_in_statusdb(self) -> bool:
        """Checks if flow cell exists in statusdb"""
        if self._exists_in_statusdb is None:
            self._exists_in_statusdb: bool = self.status_db.flowcell(self.id) is not None
            if not self._exists_in_statusdb:
                LOG.warning("Flow cell %s does not exist in statusdb!", self.id)
        return self._exists_in_statusdb

    @property
    def fastq_files_exist_in_housekeeper(self) -> bool:
        """Checks if the flow cell has any fastq files in Housekeeper"""
        if self._fastq_files_exist_in_housekeeper is None:
            self._fastq_files_exist_in_housekeeper: bool = len(self.hk_fastq_files) > 0
            if not self._fastq_files_exist_in_housekeeper:
                LOG.warning("Flow cell %s does not have any fastq files in Housekeeper!", self.id)
        return self._fastq_files_exist_in_housekeeper

    @property
    def spring_files_exist_in_housekeeper(self) -> bool:
        """Checks if the flow cell has any spring files in Housekeeper"""
        if self._spring_files_exist_in_housekeeper is None:
            self._spring_files_exist_in_housekeeper: bool = len(self.hk_spring_files) > 0
            if not self._spring_files_exist_in_housekeeper:
                LOG.warning("Flow cell %s does not have any spring files in Housekeeper!", self.id)
        return self._spring_files_exist_in_housekeeper

    @property
    def files_exist_in_housekeeper(self) -> bool:
        """Checks if the flow cell has any files, either fastq or spring, in Housekeeper"""
        if self._files_exist_in_housekeeper is None:
            self._files_exist_in_housekeeper: bool = (
                self.fastq_files_exist_in_housekeeper or self.spring_files_exist_in_housekeeper
            )
            if not self._files_exist_in_housekeeper:
                LOG.warning(
                    "Flow cell %s has neither fastq files nor spring files in Housekeeper!", self.id
                )
        return self._files_exist_in_housekeeper

    @staticmethod
    def _check_files_existence(files: list) -> List[bool]:
        """Checks file existence and handles permission errors"""
        files_exist: List[bool] = []
        for file in files:
            try:
                files_exist.append(Path(file.path).exists())
            except PermissionError:
                LOG.warning("Can't check file %s, no permission!", file)
                continue
        return files_exist

    @property
    def files_exist_on_disk(self) -> bool:
        """Checks if the spring or fastq files that are in Housekeeper are actually present on
        disk"""

        if self._files_exist_on_disk is None:
            if not self.files_exist_in_housekeeper:
                LOG.warning(
                    "Flow cell %s has no fastq files or spring files in Housekeeper, skipping "
                    "disk check",
                    self.id,
                )
            else:
                if self.fastq_files_exist_in_housekeeper:
                    fastq_files_exist_on_disk: List[bool] = self._check_files_existence(
                        self.hk_fastq_files
                    )
                    self._files_exist_on_disk: bool = all(fastq_files_exist_on_disk)
                if self.spring_files_exist_in_housekeeper:
                    spring_files_exist_on_disk: List[bool] = self._check_files_existence(
                        self.hk_spring_files
                    )
                    self._files_exist_on_disk: bool = all(spring_files_exist_on_disk)
                if not self._files_exist_on_disk:
                    LOG.warning("Flow cell %s has no fastq files or spring files on disk!", self.id)

        return self._files_exist_on_disk

    @property
    def passed_check(self) -> bool:
        """Indicates if all checks have passed"""
        if self._passed_check is None:
            LOG.info(f"Checking {self.path}:")
            self._passed_check = all(
                [
                    self.is_correctly_named,
                    self.exists_in_statusdb,
                    self.files_exist_in_housekeeper,
                    self.files_exist_on_disk,
                ]
            )
            LOG.info(
                "Flow cell %s has passed all checks, setting flag to True!", self.id
            ) if self._passed_check else LOG.info(
                "Flow cell %s failed one or more tests, setting flag to %s!",
                self.id,
                self.passed_check,
            )
        return self._passed_check

    def remove_files_from_housekeeper(self):
        """Remove fastq files and the sample sheet from Housekeeper when deleting a
        flow cell from demultiplexed-runs"""
        if self.fastq_files_exist_in_housekeeper:
            for fastq_file in self.hk_fastq_files:
                LOG.info(f"Removing {fastq_file} from Housekeeper.")
                self.hk.delete_file(fastq_file.id)
            sample_sheets = self.hk.files(tags=[self.id, HousekeeperTags.SAMPLESHEET])
            for sample_sheet in sample_sheets:
                LOG.info(f"Removing {sample_sheet} from Housekeeper.")
                self.hk.delete_file(sample_sheet.id)
        self.hk.commit()

    def remove_from_demultiplexed_runs(self):
        """Removes a flow cell directory completely from demultiplexed-runs"""
        shutil.rmtree(self.path, ignore_errors=True)
        if self.exists_in_statusdb and self.is_correctly_named:
            self.status_db.flowcell(self.id).status = FlowCellStatus.REMOVED
        self.status_db.commit()

    def remove_failed_flow_cell(self):
        """Performs the two removal actions for failed flow cells"""
        self.remove_from_demultiplexed_runs()
        if self.files_exist_in_housekeeper and self.is_correctly_named:
            self.remove_files_from_housekeeper()

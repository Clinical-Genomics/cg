"""Module that handles data and information regarding flowcells and flowcell directories. used to
inspect and clean flowcell directories in demultiplexed runs """
import logging
import re
import shutil
from pathlib import Path
from typing import Iterable, List

from housekeeper.store import models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


class DemultiplexedRunsFlowcell:
    """Class to check if a given flowcell in demultiplexed-runs is valid, or can be removed. A
    valid flowcell is named correctly, has the correct status ('ondisk') in statusdb,
    and has fastq files in Housekeeper"""

    def __init__(
        self,
        flowcell_path: Path,
        status_db: Store,
        housekeeper_api: HousekeeperAPI,
    ):
        self.status_db: Store = status_db
        self.hk: HousekeeperAPI = housekeeper_api
        self.path: Path = flowcell_path
        self.name: str = self.path.name
        self.split_name: List[str] = re.split("[_.]", self.name)
        self.identifier: str = self.split_name[3]
        self.id: str = self.identifier[1:]
        self._hk_fastq_files = None
        self._is_correctly_named = None
        self._exists_in_statusdb = None
        self._fastq_files_exist_in_housekeeper = None
        self._fastq_files_exist_on_disk = None
        self._passed_check = None

    @property
    def hk_fastq_files(self) -> Iterable[hk_models.File]:
        """All fastq files in Housekeeper for a particular flowcell"""
        if not self._hk_fastq_files:
            self._hk_fastq_files = self.hk.files(tags=[self.id, "fastq"])
        return self._hk_fastq_files

    @property
    def is_correctly_named(self) -> bool:
        """checks if the flowcell directory is correctly named: it should end with the flowcell
        id"""
        if self._is_correctly_named is None:
            self._is_correctly_named: bool = self.split_name[-1] == self.identifier
            if not self._is_correctly_named:
                LOG.warning("Flowcell name not correctly named!: %s", self.path)
                return self._is_correctly_named
        return self._is_correctly_named

    @property
    def exists_in_statusdb(self) -> bool:
        """checks if flowcell exists in statusdb"""
        if self._exists_in_statusdb is None:
            self._exists_in_statusdb: bool = self.status_db.flowcell(self.id) is not None
            if not self._exists_in_statusdb:
                LOG.warning("Flowcell %s does not exist in statusdb!", self.id)
        return self._exists_in_statusdb

    @property
    def fastq_files_exist_in_housekeeper(self) -> bool:
        """Checks if the flowcell has any fastq files in Housekeeper"""
        if self._fastq_files_exist_in_housekeeper is None:
            self._fastq_files_exist_in_housekeeper: bool = self.hk_fastq_files.count() > 0
            if not self._fastq_files_exist_in_housekeeper:
                LOG.warning("Flowcell %s does not have any fastq files in Housekeeper!", self.id)
        return self._fastq_files_exist_in_housekeeper

    @property
    def fastq_files_exist_on_disk(self) -> bool:
        """Checks if the fastq files that are in Housekeeper are actually present on disk"""
        if self._fastq_files_exist_on_disk is None:
            if not self.fastq_files_exist_in_housekeeper:
                LOG.warning(
                    "Flowcell %s has no fastq files in Housekeeper, skipping disk check", self.id
                )
                self._fastq_files_exist_on_disk = False
            else:
                self._fastq_files_exist_on_disk: bool = all(
                    [Path(fastq_file.path).exists() for fastq_file in self.hk_fastq_files]
                )
        return self._fastq_files_exist_on_disk

    @property
    def passed_check(self) -> bool:
        """indicates if all checks have passed"""
        if self._passed_check is None:
            self._passed_check = all(
                [
                    self.is_correctly_named,
                    self.exists_in_statusdb,
                    self.fastq_files_exist_in_housekeeper,
                    self.fastq_files_exist_on_disk,
                ]
            )
        return self._passed_check

    def check_existing_flowcell_directory(self):
        """performs a series of checks on the flowcell directory"""
        if not self.passed_check:
            LOG.info(
                "Flowcell %s failed one or more tests, setting flag to %s!",
                self.id,
                self.passed_check,
            )

    def remove_files_from_housekeeper(self):
        """Remove fastq files and the sample sheet from Housekeeper when deleting a flowcell from
        demultiplexed-runs"""
        for fastq_file in self.hk_fastq_files:
            self.hk.delete_file(fastq_file.id)
        sample_sheets = self.hk.files(tags=[self.id, "samplesheet"])
        for sample_sheet in sample_sheets:
            self.hk.delete_file(sample_sheet.id)

    def remove_from_demultiplexed_runs(self):
        """Removes a flowcell directory completely from demultiplexed-runs"""
        shutil.rmtree(self.path, ignore_errors=True)
        if self.exists_in_statusdb and self.is_correctly_named:
            self.status_db.flowcell(self.id).status = "removed"

"""Module that handles data and information regarding flowcells and flowcell directories. used to
inspect and clean flowcell directories in demultiplexed runs """
import logging
import re
import shutil
from pathlib import Path
from typing import List, Optional

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


class DemuxedFlowcell:
    """Class to check if a given flowcell in demultiplexed-runs is valid, or can be removed. A
    valid flowcell is named correctly, has the correct status ('ondisk') in statusdb,
    and has been successfully analysed"""

    def __init__(
        self,
        flowcell_path: Path,
        status_db: Store,
        housekeeper_api: HousekeeperAPI,
    ):
        self.path: Path = flowcell_path
        self.name: str = self.path.name
        self.split_name: List[str] = re.split("[_.]", self.name)
        self.identifier: str = self.split_name[3]
        self.id: str = self.identifier[1:]
        self.status_db: Store = status_db
        self.hk: HousekeeperAPI = housekeeper_api
        self.is_correctly_named: bool = True
        self.exists_in_status_db: bool = True
        self.status_is_on_disk: bool = True
        self.fastq_files_exist_in_housekeeper: bool = True
        self.fastq_files_exist_on_disk: bool = True
        self.passed_check: bool = True

    def check_flowcell_naming(self) -> bool:
        """checks if the flowcell directory is correctly named: it should end with the flowcell
        id"""
        self.is_correctly_named: bool = self.split_name[-1] == self.identifier
        if not self.is_correctly_named:
            LOG.warning("Flowcell name not correctly named!: %s", self.path)
        return self.is_correctly_named

    def check_flowcell_exists_in_status_db(self) -> None:
        """checks if flowcell exists in statusdb"""
        self.exists_in_status_db: bool = self.status_db.flowcell(self.id) is not None
        if not self.exists_in_status_db:
            LOG.warning("Flowcell %s does not exist in statusdb!", self.id)

    @property
    def flowcell_status(self) -> Optional[str]:
        """Returns the flowcell status in statusdb"""
        try:
            return self.status_db.flowcell(self.id).status
        except AttributeError:
            return

    def check_fastq_files_in_housekeeper(self) -> None:
        """Checks if the flowcell has any fastq files in Housekeeper"""
        self.fastq_files_exist_in_housekeeper = self.hk.files(tags=[self.id, "fastq"]).count() > 0
        if not self.fastq_files_exist_in_housekeeper:
            LOG.warning("Flowcell %s does not have any fastq files in Housekeeper!", self.id)
            self.fastq_files_exist_on_disk = False

    def check_fastq_files_on_disk(self):
        """Checks if the fastq files that are in Housekeeper are actually present on disk"""
        if self.fastq_files_exist_in_housekeeper:
            fastq_files = self.hk.files(tags=[self.id, "fastq"])
            self.fastq_files_exist_on_disk = all(
                [Path(fastq_file.path).exists() for fastq_file in fastq_files]
            )
            if not self.fastq_files_exist_on_disk:
                LOG.warning("Flowcell %s has fastq files in Housekeeper, but not on disk!", self.id)

    def check_all_checks(self):
        """Checks if all checks are passed"""
        self.passed_check = all(
            [
                self.is_correctly_named,
                self.exists_in_status_db,
                self.status_is_on_disk,
                self.fastq_files_exist_in_housekeeper,
                self.fastq_files_exist_on_disk,
            ]
        )
        if not self.passed_check:
            LOG.info(
                "Flowcell %s failed one or more tests, setting flag to %s!",
                self.id,
                self.passed_check,
            )

    def check_existing_flowcell_directory(self):
        """performs a series of checks on the flowcell directory"""
        self.check_flowcell_naming()
        self.check_flowcell_exists_in_status_db()
        self.check_fastq_files_in_housekeeper()
        self.check_fastq_files_on_disk()
        self.check_all_checks()

    def remove_files_from_housekeeper(self):
        """Remove fastq files and the sample sheet from Housekeeper when deleting a flowcell from
        demultiplexed-runs"""
        fastq_files = self.hk.files(tags=[self.id, "fastq"])
        for fastq_file in fastq_files:
            self.hk.delete_file(fastq_file.id)
        sample_sheets = self.hk.files(tags=[self.id, "samplesheet"])
        for sample_sheet in sample_sheets:
            self.hk.delete_file(sample_sheet.id)

    def remove_from_demultiplexed_runs(self):
        """Removes a flowcell directory completely from demultiplexed-runs"""
        shutil.rmtree(self.path, ignore_errors=True)
        if self.status_is_on_disk and self.is_correctly_named:
            self.status_db.flowcell(self.id).status = "removed"
        if self.fastq_files_exist_in_housekeeper:
            self.remove_files_from_housekeeper()

"""Module that handles data and information regarding flow cells and flow cell directories. Used to
inspect and clean flow cell directories in demultiplexed runs."""
import logging
import re
import shutil
from pathlib import Path
from typing import List, Optional

from alchy import Query
from housekeeper.store import models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import FlowCellStatus
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.sequencing import Sequencers, sequencer_types
from cg.constants.symbols import ASTERISK
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.store import Store

FLOW_CELL_IDENTIFIER_POSITION = 3
LOG = logging.getLogger(__name__)
SEQUENCER_IDENTIFIER_POSITION = 1


class DemultiplexedRunsFlowCell:
    """Class to check if a given flow cell in demultiplexed-runs is valid, or can be removed. A
    valid flow cell is named correctly, has the correct status ('ondisk') in Statusdb,
    and has FASTQ and/or SPRING files in Housekeeper.

    A flow cell that is correctly named has four segments divided by underscores:
    <run_date>_<sequencer>_<run_number>_<identifier>. The identifier consists of the position of
    the flow cell on the sequencer in the first position (either A or B), and the flow cell id in
    the rest of the identifier. Flow cell id is the naming convention used in Statusdb and other
    systems"""

    def __init__(
        self,
        flow_cell_path: Path,
        status_db: Store,
        housekeeper_api: HousekeeperAPI,
        trailblazer_api: Optional[TrailblazerAPI] = None,
        sample_sheets_dir: Optional[str] = None,
        fastq_files: Optional[Query] = None,
        spring_files: Optional[Query] = None,
    ):
        self.sample_sheets_dir: Path = Path(sample_sheets_dir) if sample_sheets_dir else None
        self.path: Path = flow_cell_path
        self.status_db: Store = status_db
        self.hk: HousekeeperAPI = housekeeper_api
        self.tb: TrailblazerAPI = trailblazer_api
        self.all_fastq_files: Optional[Query] = fastq_files
        self.all_spring_files: Optional[Query] = spring_files
        self.run_name: str = self.path.name
        self.split_name: List[str] = re.split("[_.]", self.run_name)
        self.identifier: str = self.split_name[FLOW_CELL_IDENTIFIER_POSITION]
        self.sequencer_serial_number: str = self.split_name[SEQUENCER_IDENTIFIER_POSITION]
        self.id: str = self.identifier[1:]
        self._hk_fastq_files: Optional[list] = None
        self._hk_spring_files: Optional[list] = None
        self._is_correctly_named: Optional[bool] = None
        self._exists_in_statusdb: Optional[bool] = None
        self._fastq_files_exist_in_housekeeper: Optional[bool] = None
        self._spring_files_exist_in_housekeeper: Optional[bool] = None
        self._files_exist_in_housekeeper: Optional[bool] = None
        self._files_exist_on_disk: Optional[bool] = None
        self._passed_check: Optional[bool] = None
        self._sequencer_type: Optional[str] = None
        self._is_demultiplexing_ongoing_or_started_and_not_completed: Optional[bool] = None

    @property
    def sequencer_type(self) -> str:
        """The type of sequencer a flow cell has been sequenced on."""
        if self._sequencer_type is None:
            self._sequencer_type: str = sequencer_types.get(
                self.sequencer_serial_number, Sequencers.OTHER
            )
        return self._sequencer_type

    @property
    def hk_fastq_files(self) -> list:
        """All FASTQ files in Housekeeper for a particular flow cell."""
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
        id."""
        if self._is_correctly_named is None:
            self._is_correctly_named: bool = self.split_name[-1] == self.identifier
            if not self._is_correctly_named:
                LOG.warning(f"Flow cell not correctly named!: {self.path}")
        return self._is_correctly_named

    @property
    def exists_in_statusdb(self) -> bool:
        """Checks if flow cell exists in Statusdb."""
        if self._exists_in_statusdb is None:
            self._exists_in_statusdb: bool = self.status_db.get_flow_cell(self.id) is not None
            if not self._exists_in_statusdb:
                LOG.warning(f"Flow cell {self.id} does not exist in Statusdb!")
        return self._exists_in_statusdb

    @property
    def fastq_files_exist_in_housekeeper(self) -> bool:
        """Checks if the flow cell has any FASTQ files in Housekeeper."""
        if self._fastq_files_exist_in_housekeeper is None:
            self._fastq_files_exist_in_housekeeper: bool = len(self.hk_fastq_files) > 0
            if not self._fastq_files_exist_in_housekeeper:
                LOG.warning(f"Flow cell {self.id} does not have any FASTQ files in Housekeeper!")
        return self._fastq_files_exist_in_housekeeper

    @property
    def spring_files_exist_in_housekeeper(self) -> bool:
        """Checks if the flow cell has any SPRING files in Housekeeper."""
        if self._spring_files_exist_in_housekeeper is None:
            self._spring_files_exist_in_housekeeper: bool = len(self.hk_spring_files) > 0
            if not self._spring_files_exist_in_housekeeper:
                LOG.warning(f"Flow cell {self.id} does not have any SPRING files in Housekeeper!")
        return self._spring_files_exist_in_housekeeper

    @property
    def files_exist_in_housekeeper(self) -> bool:
        """Checks if the flow cell has any files, either FASTQ or SPRING, in Housekeeper."""
        if self._files_exist_in_housekeeper is None:
            self._files_exist_in_housekeeper: bool = (
                self.fastq_files_exist_in_housekeeper or self.spring_files_exist_in_housekeeper
            )
            if not self._files_exist_in_housekeeper:
                LOG.warning(
                    f"Flow cell {self.id} has neither FASTQ files nor SPRING files in Housekeeper!"
                )
        return self._files_exist_in_housekeeper

    @staticmethod
    def _check_files_existence(files: list) -> List[bool]:
        """Checks file existence and handles permission errors."""
        files_exist: List[bool] = []
        for file in files:
            try:
                files_exist.append(Path(file.path).exists())
            except PermissionError:
                LOG.warning(f"Can't check file {file}, no permission!")
                continue
        return files_exist

    @property
    def files_exist_on_disk(self) -> bool:
        """Checks if the SPRING or FASTQ files that are in Housekeeper are actually present on
        disk."""

        if self._files_exist_on_disk is None:
            if self.files_exist_in_housekeeper:
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
                    LOG.warning(f"Flow cell {self.id} has no fastq files or spring files on disk!")

            else:
                LOG.warning(
                    f"Flow cell {self.id} has no FASTQ files or SPRING files in Housekeeper, skipping "
                    "disk check"
                )
                self._files_exist_on_disk = False
        return self._files_exist_on_disk

    @property
    def is_demultiplexing_ongoing_or_started_and_not_completed(self) -> bool:
        """Checks demultiplexing status for a flow cell."""
        if self._is_demultiplexing_ongoing_or_started_and_not_completed is None:
            LOG.info(f"Checking demultiplexing status for flow cell {self.id}:")
            self._is_demultiplexing_ongoing_or_started_and_not_completed: bool = (
                self.tb.has_latest_analysis_started(case_id=self.id)
                or self.tb.is_latest_analysis_ongoing(case_id=self.id)
            ) and not self.tb.is_latest_analysis_completed(case_id=self.id)
            if self._is_demultiplexing_ongoing_or_started_and_not_completed:
                LOG.warning(f"Demultiplexing not fully completed for flow cell {self.id}!")
            else:
                LOG.info("Demultiplexing fully completed!")
        return self._is_demultiplexing_ongoing_or_started_and_not_completed

    @property
    def passed_check(self) -> bool:
        """Indicates if all checks have passed."""
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
                f"Flow cell {self.id} has passed all checks, setting flag to True!"
            ) if self._passed_check else LOG.error(
                f"Flow cell {self.id} failed one or more tests, setting flag to {self._passed_check}!"
            )
        return self._passed_check

    def remove_files_from_housekeeper(self) -> None:
        """Remove fastq files and the sample sheet from Housekeeper when deleting a
        flow cell from demultiplexed-runs."""
        if self.fastq_files_exist_in_housekeeper:
            for fastq_file in self.hk_fastq_files:
                LOG.info(f"Removing {fastq_file} from Housekeeper.")
                self.hk.delete_file(fastq_file.id)
            sample_sheets = self.hk.files(tags=[self.id, SequencingFileTag.SAMPLE_SHEET])
            for sample_sheet in sample_sheets:
                LOG.info(f"Removing {sample_sheet} from Housekeeper.")
                self.hk.delete_file(sample_sheet.id)
        self.hk.commit()

    def remove_from_demultiplexed_runs(self) -> None:
        """Removes a flow cell directory completely from demultiplexed-runs."""
        if self.is_correctly_named:
            self.archive_sample_sheet()
        shutil.rmtree(self.path, ignore_errors=True)
        if self.exists_in_statusdb and self.is_correctly_named:
            self.status_db.get_flow_cell(self.id).status = FlowCellStatus.REMOVED
        self.status_db.commit()

    def remove_failed_flow_cell(self) -> None:
        """Performs the two removal actions for failed flow cells."""
        self.remove_from_demultiplexed_runs()
        if self.files_exist_in_housekeeper and self.is_correctly_named:
            self.remove_files_from_housekeeper()

    def archive_sample_sheet(self) -> None:
        """Archives a sample sheet to /home/proj/production/sample_sheets and adds it to
        Housekeeper with an appropriate tag."""
        LOG.info(f"Archiving sample sheet for flow cell {self.run_name}")
        globbed_unaligned_paths: Path.glob = Path(self.path).glob(
            DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME + ASTERISK
        )
        globbed_unaligned_paths_list: list = list(globbed_unaligned_paths)
        if not globbed_unaligned_paths_list:
            LOG.warning(
                f"No Unaligned directory found for flow cell {self.run_nam}! No sample sheet to archive!"
            )
            return
        unaligned_path: Path = globbed_unaligned_paths_list[0]
        original_sample_sheet: Path = (
            Path(
                unaligned_path,
                DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME,
            )
            if self.sequencer_type == Sequencers.NOVASEQ
            else Path(self.path, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)
        )

        sample_sheet_run_dir: Path = Path(self.sample_sheets_dir, self.run_name)
        archived_sample_sheet: Path = Path(
            sample_sheet_run_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
        )

        sample_sheet_run_dir.mkdir(parents=True, exist_ok=True)
        LOG.info(f"Sample sheet directory created for flow cell directory {self.run_name}")

        try:
            shutil.move(original_sample_sheet, archived_sample_sheet)
            self.add_sample_sheet_to_housekeeper(archived_sample_sheet)
            self.hk.commit()
        except FileNotFoundError:
            LOG.warning(f"No sample sheet found in flow cell directory {self.run_name}!")
            shutil.rmtree(sample_sheet_run_dir, ignore_errors=True)

    def add_sample_sheet_to_housekeeper(self, sample_sheet_path: Path):
        """Adds an archive sample sheet to Housekeeper."""

        hk_bundle: hk_models.Bundle = self.hk.bundle(self.id)
        if hk_bundle is None:
            hk_bundle = self.hk.create_new_bundle_and_version(name=self.id)

        with self.hk.session_no_autoflush():
            hk_version: hk_models.Version = self.hk.last_version(bundle=hk_bundle.name)
            if self.hk.files(path=str(sample_sheet_path)).first() is None:
                LOG.info(f"Adding archived sample sheet: {str(sample_sheet_path)}")
                tags: List[str] = [SequencingFileTag.ARCHIVED_SAMPLE_SHEET, self.id]
                self.hk.add_file(path=str(sample_sheet_path), version_obj=hk_version, tags=tags)
        self.hk.commit()

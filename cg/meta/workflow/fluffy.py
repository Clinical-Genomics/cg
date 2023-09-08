import datetime as dt
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy.orm import Query
from cg.constants import Pipeline
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import SampleSheetBCLConvertSections, SampleSheetBcl2FastqSections
from cg.exc import HousekeeperFileMissingError
from cg.io.controller import ReadFile
from cg.meta.demultiplex.housekeeper_storage_functions import get_sample_sheets_from_latest_version
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.fluffy import FluffySampleSheet, FluffySampleSheetEntry, FluffySampleSheetHeader
from cg.store.models import Family, Flowcell, Sample
from cg.utils import Process
from cg.io.sample_sheet import read_sample_sheet

LOG = logging.getLogger(__name__)


def get_data_header_key(sample_sheet: Dict[str, List[str]]) -> str:
    """
    Get the data header key from a sample sheet.

    The data header key is the key in the sample sheet dictionary that corresponds to the data section of the sample sheet.

    Args:
        sample_sheet: A dictionary representing the sample sheet.

    Returns:
        The data header key.

    Raises:
        ValueError: If the data header key cannot be found in the sample sheet.
    """
    sample_sheet_headers: List[List[str]] = [
        SampleSheetBCLConvertSections.Data.HEADER.value,
        SampleSheetBcl2FastqSections.Data.HEADER.value,
    ]
    data_header_key = next((key for key in sample_sheet if key in sample_sheet_headers), None)
    if not data_header_key:
        LOG.error(
            f"Sample sheet data header is missing!\n"
            f"Cannot find any of {sample_sheet_headers} in the samplesheet!"
        )
        raise ValueError
    return data_header_key


def get_column_names(sample_sheet: Dict[str, List[str]], data_header_key: str) -> List[str]:
    """
    Get the column names from a sample sheet data section.

    Args:
        sample_sheet: A dictionary representing the sample sheet.
        data_header_key: The key in the sample sheet dictionary that corresponds to the data section.

    Returns:
        A list of column names from the sample sheet data section.
    """
    return sample_sheet[data_header_key][0]


def validate_sample_sheet_column_names(sample_sheet_column_names: List[str]) -> None:
    """Validate that the sample sheet columns matches the expected format."""
    expected_column_names = [
        set(SampleSheetBCLConvertSections.Data.COLUMN_NAMES.value),
        set(SampleSheetBcl2FastqSections.Data.COLUMN_NAMES.value),
    ]
    if all(
        set(sample_sheet_column_names) != expected
        for expected in expected_column_names
    ):
        LOG.error("Sample sheet data header does not match expected format!")
        raise ValueError


class FluffyAnalysisAPI(AnalysisAPI):
    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.FLUFFY,
    ):
        self.root_dir = Path(config.fluffy.root_dir)
        LOG.info("Set root dir to %s", config.fluffy.root_dir)
        self.fluffy_config = Path(config.fluffy.config_path)
        super().__init__(
            pipeline,
            config,
        )

    @property
    def threshold_reads(self):
        return False

    @property
    def process(self) -> Process:
        if not self._process:
            self._process = Process(binary=self.config.fluffy.binary_path)
        return self._process

    def get_case_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id)

    def get_sample_sheet_path(self, case_id: str) -> Path:
        """
        Location in case folder where sample sheet is expected to be stored. Sample sheet is used as a config
        required to run Fluffy
        """
        starlims_id: str = (
            self.status_db.get_case_by_internal_id(internal_id=case_id).links[0].sample.order
        )
        return Path(self.root_dir, case_id, f"SampleSheet_{starlims_id}.csv")

    def get_workdir_path(self, case_id: str) -> Path:
        """
        Location in case folder where all sub-folders for each sample containing fastq files are to e saved
        """
        return Path(self.root_dir, case_id, "fastq")

    def get_fastq_path(self, case_id: str, sample_id: str) -> Path:
        """
        Location in working directory to which fastq files are saved for each sample separately
        """
        return Path(self.get_workdir_path(case_id), sample_id)

    def get_output_path(self, case_id: str) -> Path:
        """
        Location in case directory where Fluffy outputs will be stored
        """
        return Path(self.root_dir, case_id, "output")

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """
        Location in working directory where deliverables file will be stored upon completion of analysis.
        Deliverables file is used to communicate paths and tag definitions for files in a finished analysis
        """
        return Path(self.get_output_path(case_id), "deliverables.yaml")

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        """
        Location in working directory where SLURM job id file is to be stored.
        This file contains SLURM ID of jobs associated with current analysis ,
        is used as a config to be submitted to Trailblazer and track job progress in SLURM
        """
        return Path(self.get_output_path(case_id), "sacct", "submitted_jobs.yaml")

    def get_analysis_finish_path(self, case_id: str) -> Path:
        return Path(self.get_output_path(case_id), "COMPLETE")

    def link_fastq_files(self, case_id: str, dry_run: bool = False) -> None:
        """
        Links fastq files from Housekeeper to case working directory
        """
        case_obj: Family = self.status_db.get_case_by_internal_id(internal_id=case_id)
        latest_flow_cell = self.status_db.get_latest_flow_cell_on_case(family_id=case_id)
        workdir_path = self.get_workdir_path(case_id=case_id)
        if workdir_path.exists() and not dry_run:
            LOG.info("Fastq directory exists, removing and re-linking files!")
            shutil.rmtree(workdir_path, ignore_errors=True)
        workdir_path.mkdir(parents=True, exist_ok=True)
        for family_sample in case_obj.links:
            sample_id = family_sample.sample.internal_id
            files: Query = self.housekeeper_api.files(
                bundle=sample_id, tags=["fastq", latest_flow_cell.name]
            )

            sample_path: Path = self.get_fastq_path(case_id=case_id, sample_id=sample_id)
            for file in files:
                if not dry_run:
                    Path.mkdir(sample_path, exist_ok=True, parents=True)
                    Path(sample_path / Path(file.full_path).name).symlink_to(file.full_path)
                LOG.info(f"Linking {file.full_path} to {sample_path / Path(file.full_path).name}")

    def get_concentrations_from_lims(self, sample_id: str) -> str:
        """Get sample concentration from LIMS"""
        return self.lims_api.get_sample_attribute(lims_id=sample_id, key="concentration_sample")

    def get_sample_control_status(self, sample_id: str) -> bool:
        sample_obj: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        return bool(sample_obj.control)

    def generate_fluffy_sample_sheet(
        self,
        flow_cell_id: str,
        sample_sheet_housekeeper_path: Path,
    ) -> None:
        """
        Generate a Fluffy sample sheet for a case.
        """

        sample_sheet: Dict[str, List[str]] = read_sample_sheet(sample_sheet_housekeeper_path)
        data_header_key: str = get_data_header_key(sample_sheet)
        sample_sheet_column_names: List[str] = get_column_names(sample_sheet=sample_sheet, data_header_key=data_header_key)
        validate_sample_sheet_column_names(sample_sheet_column_names)

        sample_data = [
            dict(zip(sample_sheet_column_names, sample))
            for sample in sample_sheet[data_header_key][1:]
        ]

        fluffy_sample_sheet_data_entries = []
        for sample in sample_data:
            sample_internal_id = sample.get("Sample_ID") or sample.get("SampleID")
            statusdb_sample = self.status_db.get_sample_by_internal_id(sample_internal_id)
            fluffy_sample_sheet_data_entry = {
                "sample_internal_id": sample_internal_id,
                "flow_cell_id": flow_cell_id,
                "lane": sample["Lane"],
                "index": sample.get("index") or sample.get("Index"),
                "index2": sample.get("index2") or sample.get("Index2"),
                "sample_name": statusdb_sample.name,
                "sample_project": statusdb_sample.order,
                "exclude": self.get_sample_control_status(sample_id=sample_internal_id),
                "library_nM": self.get_concentrations_from_lims(sample_id=sample_internal_id),
                "sequencing_date": statusdb_sample.sequencing_date.date(),
            }
            fluffy_sample_sheet_data_entries.append(
                FluffySampleSheetEntry(**fluffy_sample_sheet_data_entry)
            )

        return FluffySampleSheet(
            header=FluffySampleSheetHeader, entries=fluffy_sample_sheet_data_entries
        )

    def get_sample_sheet_housekeeper_path(self, flowcell_name: str) -> Path:
        """Returns the path to original sample sheet file that is added to Housekeeper."""
        sample_sheet_files: list = get_sample_sheets_from_latest_version(
            flow_cell_id=flowcell_name, hk_api=self.housekeeper_api
        )
        if not sample_sheet_files:
            LOG.error(
                f"Sample sheet file for flowcell {flowcell_name} could not be found in Housekeeper!"
            )
            raise HousekeeperFileMissingError
        return Path(sample_sheet_files[0].full_path)

    def make_sample_sheet(self, case_id: str, dry_run: bool) -> None:
        """
        Create SampleSheet.csv file in working directory and add desired values to the file
        """
        latest_flow_cell: Flowcell = self.status_db.get_latest_flow_cell_on_case(family_id=case_id)
        sample_sheet_housekeeper_path = self.get_sample_sheet_housekeeper_path(
            flowcell_name=latest_flow_cell.name
        )
        sample_sheet_workdir_path = Path(self.get_sample_sheet_path(case_id=case_id))
        LOG.info(
            "Writing modified csv from %s to %s",
            sample_sheet_housekeeper_path,
            sample_sheet_workdir_path,
        )
        if not dry_run:
            Path(self.root_dir, case_id).mkdir(parents=True, exist_ok=True)
            fluffy_sample_sheet: FluffySampleSheet = self.generate_fluffy_sample_sheet(
                flow_cell_id=latest_flow_cell.name,
                sample_sheet_housekeeper_path=sample_sheet_housekeeper_path,
            )
            LOG.info(
                "Writing modified csv from %s to %s",
                sample_sheet_housekeeper_path,
                sample_sheet_workdir_path,
            )
            fluffy_sample_sheet.write_sample_sheet(sample_sheet_workdir_path)

    def run_fluffy(
        self, case_id: str, dry_run: bool, workflow_config: str, external_ref: bool = False
    ) -> None:
        """
        Call fluffy with the configured command-line arguments
        """
        output_path: Path = self.get_output_path(case_id=case_id)
        if output_path.exists():
            LOG.info("Old working directory found, cleaning!")
            if not dry_run:
                shutil.rmtree(output_path, ignore_errors=True)
        if not workflow_config:
            workflow_config = self.fluffy_config.as_posix()
        if not external_ref:
            batch_ref_flag = "--batch-ref"
        else:
            batch_ref_flag = ""
        command_args = [
            "--config",
            workflow_config,
            "--sample",
            self.get_sample_sheet_path(case_id=case_id).as_posix(),
            "--project",
            self.get_workdir_path(case_id=case_id).as_posix(),
            "--out",
            self.get_output_path(case_id=case_id).as_posix(),
            "--analyse",
            batch_ref_flag,
            "--slurm_params",
            self.get_slurm_param_qos(case_id=case_id),
        ]
        self.process.run_command(command_args, dry_run=dry_run)

    def get_cases_to_store(self) -> List[Family]:
        """Return cases where analysis finished successfully,
        and is ready to be stored in Housekeeper."""
        return [
            case
            for case in self.status_db.get_running_cases_in_pipeline(pipeline=self.pipeline)
            if Path(self.get_analysis_finish_path(case_id=case.internal_id)).exists()
        ]

    def get_slurm_param_qos(self, case_id):
        return f"qos:{self.get_slurm_qos_for_case(case_id=case_id)}"

import datetime as dt
import logging
import shutil
from enum import Enum
from pathlib import Path
from typing import List, Optional

import pandas as pd
from pydantic import BaseModel
from sqlalchemy.orm import Query

from cg.apps.demultiplex.sample_sheet.models import FlowCellSampleBCLConvert, SampleSheet
from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_sample_sheet_from_file,
    get_sample_type_from_sequencer_type,
)
from cg.constants import Pipeline
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import SampleSheetBcl2FastqSections
from cg.exc import HousekeeperFileMissingError
from cg.io.controller import ReadFile
from cg.meta.demultiplex.housekeeper_storage_functions import get_sample_sheets_from_latest_version
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Family, Flowcell, Sample
from cg.utils import Process

LOG = logging.getLogger(__name__)


class FluffySampleSheetHeaders(Enum):
    flow_cell_id: str = "FCID"
    lane: str = "Lane"
    sample_internal_id: str = "Sample_ID"
    sample_reference: str = "SampleRef"
    index: str = "index"
    index2: str = "index2"
    sample_name: str = "SampleName"
    control: str = "Control"
    recipe: str = "Recipe"
    operator: str = "Operator"
    sample_project: str = "SampleProject"
    exclude: str = "Exclude"
    library_nM: str = "Library_nM"
    sequencing_date: str = "SequencingDate"


class FluffySampleSheetEntry(BaseModel):
    flow_cell_id: str
    lane: int
    sample_internal_id: str
    sample_reference: str = "hg19"
    index: str
    index2: str
    sample_name: str
    control: Optional[str] = "N"
    recipe: Optional[str] = "R1"
    operator: Optional[str] = "script"
    sample_project: str
    exclude: bool
    library_nM: float
    sequencing_date: dt.date


class FluffySampleSheet(BaseModel):
    entries: List[FluffySampleSheetEntry]

    def write_sample_sheet(self, out_path: Path) -> None:
        LOG.info("Writing fluffy sample sheet to {sample_sheet_out_path}")
        with out_path.open("w") as outfile:
            outfile.write(",".join([header.value for header in FluffySampleSheetHeaders]) + "\n")
            for entry in self.entries:
                outfile.write(",".join(str(value) for value in entry.model_dump().values()) + "\n")


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

    def get_sample_starlims_id(self, sample_id: str) -> str:
        sample_obj: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        return sample_obj.order

    def get_sample_sequenced_date(self, sample_id: str) -> Optional[dt.date]:
        sample_obj: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        sequenced_at: dt.datetime = sample_obj.sequenced_at
        if sequenced_at:
            return sequenced_at.date()

    def get_sample_control_status(self, sample_id: str) -> bool:
        sample_obj: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        return bool(sample_obj.control)

    def get_sample_order(self, sample_id: str) -> str:
        sample_obj: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        return sample_obj.order

    def get_nr_of_header_lines_in_sample_sheet(
        self,
        sample_sheet_housekeeper_path: Path,
    ) -> int:
        """
        Return the number of header lines in a Fluffy sample sheet.
        Any lines before and including the line starting with [Data] is considered the header.

        Returns:
        int: The number of lines before the sample sheet data header
        """
        sample_sheet_content: List[List[str]] = ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=sample_sheet_housekeeper_path
        )
        header_line_count: int = 1
        for line in sample_sheet_content:
            if SampleSheetBcl2FastqSections.Data.HEADER.value in line:
                break
            header_line_count += 1
        return header_line_count

    def read_sample_sheet_data(self, sample_sheet_housekeeper_path: Path) -> pd.DataFrame:
        """
        Read in a sample sheet starting from the sample sheet data header.

        Args:
                        sample_sheet_housekeeper_path (Path): Path to the housekeeper sample sheet file

        Returns:
                        pd.DataFrame: A pandas dataframe of the sample sheet
        """
        header_line_count: int = self.get_nr_of_header_lines_in_sample_sheet(
            sample_sheet_housekeeper_path=sample_sheet_housekeeper_path
        )
        return pd.read_csv(sample_sheet_housekeeper_path, index_col=None, header=header_line_count)

    def add_sample_sheet_column(
        self, sample_sheet_df: pd.DataFrame, new_column: str, to_add: list
    ) -> pd.DataFrame:
        """Add columns to the sample sheet.
        Returns:
                        pd.DataFrame: Sample sheet pd.DataFrame.
        """
        try:
            sample_sheet_df[new_column] = to_add
        except ValueError:
            LOG.error(
                f"Error when trying to add the column: {new_column} to sample sheet with data: {to_add}."
            )
        return sample_sheet_df

    def column_has_alias(self, sample_sheet_df: pd.DataFrame, alias: str) -> bool:
        return alias in sample_sheet_df.columns

    def set_column_alias(self, sample_sheet_df: pd.DataFrame, alias: str, alternative: str) -> str:
        """Return column alias from the sample sheet or set to alternative.
        Returns: str: column name alias
        """
        return (
            alias
            if self.column_has_alias(sample_sheet_df=sample_sheet_df, alias=alias)
            else alternative
        )

    def write_sample_sheet_csv(
        self, sample_sheet_df: pd.DataFrame, sample_sheet_workdir_path: Path
    ):
        """
        Write the sample sheet as a csv file
        """
        sample_sheet_df.to_csv(
            sample_sheet_workdir_path,
            sep=",",
            index=False,
        )

    def create_fluffy_sample_sheet(
        self,
        sample_sheet: SampleSheet,
        flow_cell_id: str,
    ) -> FluffySampleSheet:
        fluffy_sample_sheet_rows = []

        for sample in sample_sheet.samples:
            sample_id: str = sample.sample_id
            db_sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)

            sample_sheet_row = FluffySampleSheetEntry(
                flow_cell_id=flow_cell_id,
                lane=sample.lane,
                sample_internal_id=sample_id,
                index=sample.index,
                index2=sample.index2,
                sample_name=db_sample.name,
                sample_project=db_sample.order,
                exclude=self.get_sample_control_status(sample_id),
                library_nM=self.get_concentrations_from_lims(sample_id),
                sequencing_date=self.get_sample_sequenced_date(sample_id),
            )
            fluffy_sample_sheet_rows.append(sample_sheet_row)

        return FluffySampleSheet(entries=fluffy_sample_sheet_rows)

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
        flow_cell: Flowcell = self.status_db.get_latest_flow_cell_on_case(case_id)
        sample_sheet_housekeeper_path: Path = self.get_sample_sheet_housekeeper_path(flow_cell.name)
        flow_cell_sample_type = get_sample_type_from_sequencer_type(flow_cell.sequencer_type)

        sample_sheet: SampleSheet = get_sample_sheet_from_file(
            infile=sample_sheet_housekeeper_path,
            flow_cell_sample_type=flow_cell_sample_type,
        )

        if not dry_run:
            Path(self.root_dir, case_id).mkdir(parents=True, exist_ok=True)
            fluffy_sample_sheet: FluffySampleSheet = self.create_fluffy_sample_sheet(
                sample_sheet=sample_sheet,
                flow_cell_id=flow_cell.name,
            )

            sample_sheet_out_path = Path(self.get_sample_sheet_path(case_id))
            fluffy_sample_sheet.write_sample_sheet(sample_sheet_out_path)

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

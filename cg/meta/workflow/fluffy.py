import datetime as dt
import logging
import shutil
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy.orm import Query

from cg.apps.demultiplex.sample_sheet.read_sample_sheet import get_flow_cell_samples_from_content
from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSample
from cg.constants import Workflow
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile, WriteFile
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Flowcell, Sample
from cg.utils import Process

LOG = logging.getLogger(__name__)


class FluffySampleSheetHeaders(StrEnum):
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
    sample_project: str = "Sample_Project"
    exclude: str = "Exclude"
    library_nM: str = "Library_nM"
    sequencing_date: str = "SequencingDate"

    @classmethod
    def headers(cls) -> list[str]:
        return list(map(lambda header: header.value, cls))


class FluffySample(BaseModel):
    flow_cell_id: str
    lane: int
    sample_internal_id: str
    sample_reference: str = "hg19"
    index: str
    index2: str
    sample_name: str
    control: str | None = "N"
    recipe: str | None = "R1"
    operator: str | None = "script"
    sample_project: str
    exclude: bool
    library_nM: float
    sequencing_date: dt.date


class FluffySampleSheet(BaseModel):
    samples: list[FluffySample]

    def write_sample_sheet(self, out_path: Path) -> None:
        LOG.info(f"Writing fluffy sample sheet to {out_path}")
        entries = [entry.model_dump().values() for entry in self.samples]
        content = [FluffySampleSheetHeaders.headers()] + entries
        WriteFile.write_file_from_content(content, FileFormat.CSV, out_path)


class FluffyAnalysisAPI(AnalysisAPI):
    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.FLUFFY,
    ):
        self.root_dir = Path(config.fluffy.root_dir)
        LOG.info("Set root dir to %s", config.fluffy.root_dir)
        self.fluffy_config = Path(config.fluffy.config_path)
        super().__init__(workflow, config)

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

    def get_job_ids_path(self, case_id: str) -> Path:
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
        case_obj: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
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

    def get_sample_sequenced_date(self, sample_id: str) -> dt.date | None:
        sample_obj: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        last_sequenced_at: dt.datetime = sample_obj.last_sequenced_at
        if last_sequenced_at:
            return last_sequenced_at.date()

    def get_sample_control_status(self, sample_id: str) -> bool:
        sample_obj: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        return bool(sample_obj.control)

    def create_fluffy_sample_sheet(
        self,
        samples: list[FlowCellSample],
        flow_cell_id: str,
    ) -> FluffySampleSheet:
        fluffy_sample_sheet_rows = []

        for sample in samples:
            sample_id: str = sample.sample_id
            db_sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)

            sample_sheet_row = FluffySample(
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

        return FluffySampleSheet(samples=fluffy_sample_sheet_rows)

    def make_sample_sheet(self, case_id: str, dry_run: bool) -> None:
        """
        Create SampleSheet.csv file in working directory and add desired values to the file
        """
        flow_cell: Flowcell = self.status_db.get_latest_flow_cell_on_case(case_id)
        sample_sheet_path: Path = self.housekeeper_api.get_sample_sheet_path(flow_cell.name)
        sample_sheet_content: list[list[str]] = ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=sample_sheet_path
        )
        samples: list[FlowCellSample] = get_flow_cell_samples_from_content(sample_sheet_content)

        if not dry_run:
            Path(self.root_dir, case_id).mkdir(parents=True, exist_ok=True)
            fluffy_sample_sheet: FluffySampleSheet = self.create_fluffy_sample_sheet(
                samples=samples,
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

    def get_cases_to_store(self) -> list[Case]:
        """Return cases where analysis finished successfully,
        and is ready to be stored in Housekeeper."""
        return [
            case
            for case in self.status_db.get_running_cases_in_workflow(workflow=self.workflow)
            if Path(self.get_analysis_finish_path(case_id=case.internal_id)).exists()
        ]

    def get_slurm_param_qos(self, case_id):
        return f"qos:{self.get_slurm_qos_for_case(case_id=case_id)}"

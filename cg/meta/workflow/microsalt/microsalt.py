import logging
import shutil
from datetime import datetime
from pathlib import Path

import rich_click as click

from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Workflow
from cg.constants.constants import FileExtensions
from cg.constants.tb import AnalysisStatus
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import MicrosaltFastqHandler
from cg.meta.workflow.microsalt.quality_controller import MicroSALTQualityController
from cg.meta.workflow.microsalt.quality_controller.models import QualityResult
from cg.meta.workflow.microsalt.utils import get_most_recent_project_directory
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.utils import Process

LOG = logging.getLogger(__name__)


class MicrosaltAnalysisAPI(AnalysisAPI):
    """API to manage Microsalt Analyses"""

    def __init__(self, config: CGConfig, workflow: Workflow = Workflow.MICROSALT):
        super().__init__(workflow, config)
        self.root_dir = config.microsalt.root
        self.queries_path = config.microsalt.queries_path
        self.quality_checker = MicroSALTQualityController(config.status_db)

    @property
    def fastq_handler(self):
        return MicrosaltFastqHandler

    @property
    def conda_binary(self) -> str:
        return self.config.microsalt.conda_binary

    @property
    def process(self) -> Process:
        if not self._process:
            self._process = Process(
                binary=self.config.microsalt.binary_path,
                conda_binary=f"{self.conda_binary}" if self.conda_binary else None,
                environment=self.config.microsalt.conda_env,
            )
        return self._process

    def clean_run_dir(
        self, case_id: str, skip_confirmation: bool, case_path: list[Path] | Path
    ) -> int:
        """Remove workflow run directories for a MicroSALT case."""

        if not case_path:
            LOG.info(
                f"There is no case paths for case {case_id}. Setting cleaned at to {datetime.now()}"
            )
            self.clean_analyses(case_id=case_id)
            return EXIT_SUCCESS
        if isinstance(case_path, Path):
            case_path: list[Path] = [case_path]
        for analysis_path in case_path:
            if skip_confirmation or click.confirm(
                f"Are you sure you want to remove all files in {analysis_path}?"
            ):
                if analysis_path.is_symlink():
                    LOG.warning(
                        f"Will not automatically delete symlink: {analysis_path}, delete it manually",
                    )
                    return EXIT_FAIL

                shutil.rmtree(analysis_path, ignore_errors=True)
                LOG.info(f"Cleaned {analysis_path}")

        self.clean_analyses(case_id=case_id)
        return EXIT_SUCCESS

    def get_case_fastq_path(self, case_id: str) -> Path:
        """Get fastq paths for a case."""
        return Path(self.root_dir, "fastq", case_id)

    def get_config_path(self, filename: str) -> Path:
        return Path(self.queries_path, filename).with_suffix(".json")

    def get_job_ids_path(self, case_id: str) -> Path:
        project_id: str = self.get_project_id(case_id)
        return Path(
            self.root_dir,
            "results",
            "reports",
            "trailblazer",
            f"{project_id}_slurm_ids{FileExtensions.YAML}",
        )

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """Returns a path where the microSALT deliverables file for the order_id should be
        located"""
        case_obj: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        order_id: str = case_obj.name
        deliverables_file_path = Path(
            self.root_dir,
            "results",
            "reports",
            "deliverables",
            f"{order_id}_deliverables.yaml",
        )
        if deliverables_file_path.exists():
            LOG.info("Found deliverables file %s", deliverables_file_path)
        return deliverables_file_path

    def get_sample_fastq_destination_dir(self, case: Case, sample: Sample) -> Path:
        return Path(self.get_case_fastq_path(case_id=case.internal_id), sample.internal_id)

    def link_fastq_files(self, case_id: str, sample_id: str | None, dry_run: bool = False) -> None:
        case_obj: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        samples: list[Sample] = self.get_samples(case_id=case_id, sample_id=sample_id)
        for sample_obj in samples:
            self.link_fastq_files_for_sample(case=case_obj, sample=sample_obj)

    def get_samples(self, case_id: str, sample_id: str | None = None) -> list[Sample]:
        """Returns a list of samples to configure
        If sample_id is specified, will return a list with only this sample_id.
        Otherwise, returns all samples in given case"""
        if sample_id:
            return [self.status_db.get_sample_by_internal_id(internal_id=sample_id)]

        case_obj: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        return [link.sample for link in case_obj.links]

    def get_cases_to_store(self) -> list[Case]:
        cases_qc_ready: list[Case] = self.get_completed_cases()
        cases_to_store: list[Case] = []
        LOG.info(f"Found {len(cases_qc_ready)} cases to perform QC on!")

        for case in cases_qc_ready:
            case_run_dir: Path | None = self.get_case_path(case.internal_id)
            LOG.info(f"Checking QC for case {case.internal_id} in {case_run_dir}")

            if self.quality_checker.is_qc_required(case_run_dir):
                LOG.info(f"QC required for case {case.internal_id}")
                metrics_file_path = self.get_metrics_file_path(case.internal_id)

                if not metrics_file_path.exists():
                    continue

                result: QualityResult = self.quality_checker.quality_control(metrics_file_path)
                self.trailblazer_api.add_comment(case_id=case.internal_id, comment=result.summary)
                if result.passes_qc:
                    cases_to_store.append(case)
                else:
                    self.trailblazer_api.set_analysis_status(
                        case_id=case.internal_id, status=AnalysisStatus.FAILED
                    )
            else:
                cases_to_store.append(case)

        return cases_to_store

    def get_completed_cases(self) -> list[Case]:
        """Return cases that are completed in trailblazer."""
        return [
            case
            for case in self.status_db.get_running_cases_in_workflow(self.workflow)
            if self.trailblazer_api.is_latest_analysis_completed(case.internal_id)
        ]

    def get_metrics_file_path(self, case_id: str) -> Path:
        """Return path to metrics file for a case."""
        project_id: str = self.get_project_id(case_id)
        case_run_dir: Path = self.get_case_path(case_id)
        return Path(case_run_dir, f"{project_id}{FileExtensions.JSON}")

    def extract_project_id(self, sample_id: str) -> str:
        return sample_id.rsplit("A", maxsplit=1)[0]

    def get_project_id(self, case_id: str) -> str:
        case: Case = self.status_db.get_case_by_internal_id(case_id)
        sample_id: str = case.links[0].sample.internal_id
        return self.extract_project_id(sample_id)

    def get_results_dir(self) -> Path:
        return Path(self.root_dir, "results")

    def get_case_path(self, case_id: str) -> Path:
        project_id: str = self.get_project_id(case_id)
        results_dir: Path = self.get_results_dir()
        return get_most_recent_project_directory(project_id=project_id, directory=results_dir)

import logging
from pathlib import Path
from typing import Optional

from cg.constants import Pipeline
from cg.constants.constants import FileExtensions, FileFormat, WorkflowManager
from cg.exc import CgError
from cg.io.controller import WriteFile
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import FastqHandler
from cg.meta.workflow.nextflow_common import NextflowAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.utils import Process

LOG = logging.getLogger(__name__)


class NfAnalysisAPI(AnalysisAPI):
    """Parent class for handling NF-core analyses."""

    def __init__(self, config: CGConfig, pipeline: Pipeline):
        super().__init__(config=config, pipeline=pipeline)
        self.pipeline: Pipeline = pipeline
        self.root_dir: Optional[str] = None
        self.nfcore_pipeline_path: Optional[str] = None
        self.references: Optional[str] = None
        self.profile: Optional[str] = None
        self.conda_env: Optional[str] = None
        self.conda_binary: Optional[str] = None
        self.tower_binary_path: Optional[str] = None
        self.tower_pipeline: Optional[str] = None
        self.account: Optional[str] = None
        self.email: Optional[str] = None
        self.compute_env: Optional[str] = None
        self.revision: Optional[str] = None

    @property
    def root(self) -> str:
        return self.root_dir

    @property
    def fastq_handler(self):
        return FastqHandler

    @property
    def process(self):
        if not self._process:
            self._process = Process(
                binary=self.tower_binary_path,
            )
        return self._process

    @process.setter
    def process(self, process: Process):
        self._process = process

    def get_profile(self, profile: Optional[str] = None) -> str:
        return profile or self.profile

    def get_workflow_manager(self) -> str:
        """Get workflow manager from Tower."""
        return WorkflowManager.Tower.value

    def get_case_path(self, case_id: str) -> Path:
        """Path to case working directory."""
        return NextflowAnalysisAPI.get_case_path(case_id=case_id, root_dir=self.root)

    def get_case_config_path(self, case_id):
        return NextflowAnalysisAPI.get_case_config_path(case_id=case_id, root_dir=self.root_dir)

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        """Return the path to a Trailblazer config file containing Tower IDs."""
        return Path(self.root_dir, case_id, "tower_ids").with_suffix(FileExtensions.YAML)

    def write_trailblazer_config(self, case_id: str, tower_id: str) -> None:
        """Write Tower IDs to a file used as the Trailblazer config."""
        config_path: Path = self.get_trailblazer_config_path(case_id=case_id)
        LOG.info(f"Writing Tower ID to {config_path.as_posix()}")
        WriteFile.write_file_from_content(
            content={case_id: [tower_id]},
            file_format=FileFormat.YAML,
            file_path=config_path,
        )

    def verify_case_config_file_exists(self, case_id: str, dry_run: bool = False) -> None:
        """Raise an error if config file is not found."""
        if not dry_run and not Path(self.get_case_config_path(case_id=case_id)).exists():
            raise ValueError(f"No config file found for case {case_id}")

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """Returns a path where the deliverables file for a case should be located."""
        return NextflowAnalysisAPI.get_deliverables_file_path(
            case_id=case_id, root_dir=self.root_dir
        )

    def verify_deliverables_file_exists(self, case_id: str) -> None:
        """Raise an error if deliverables files file is not found."""
        if not Path(self.get_deliverables_file_path(case_id=case_id)).exists():
            raise CgError(f"No deliverables file found for case {case_id}")

    def get_metrics_deliverables_path(self, case_id: str) -> Path:
        """Return a path where the <case>_metrics_deliverables.yaml file should be located."""
        return Path(self.root_dir, case_id, f"{case_id}_metrics_deliverables").with_suffix(
            FileExtensions.YAML
        )

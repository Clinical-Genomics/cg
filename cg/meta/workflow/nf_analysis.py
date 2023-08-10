import logging
import operator
from pathlib import Path
from typing import List, Optional

from cg.constants import Pipeline
from cg.constants.constants import FileExtensions, FileFormat, WorkflowManager
from cg.exc import CgError
from cg.io.controller import ReadFile, WriteFile
from cg.meta.workflow.analysis import AnalysisAPI
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
        """Get NF profiles."""
        return profile or self.profile

    def get_workflow_manager(self) -> str:
        """Get workflow manager from Tower."""
        return WorkflowManager.Tower.value

    def get_case_path(self, case_id: str) -> Path:
        """Path to case working directory."""
        return Path(self.root_dir, case_id)

    def get_case_config_path(self, case_id: str) -> Path:
        """Path to sample sheet."""
        return Path(self.get_case_path(case_id), f"{case_id}_samplesheet").with_suffix(
            FileExtensions.CSV
        )

    @staticmethod
    def get_nextflow_config_path(nextflow_config: Optional[str] = None) -> Optional[Path]:
        """Path to Nextflow config file."""
        if nextflow_config:
            return Path(nextflow_config).absolute()

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        """Return the path to a Trailblazer config file containing Tower IDs."""
        return Path(self.root_dir, case_id, "tower_ids").with_suffix(FileExtensions.YAML)

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """Path to deliverables file for a case."""
        return Path(self.get_case_path(case_id), f"{case_id}_deliverables").with_suffix(
            FileExtensions.YAML
        )

    def get_metrics_deliverables_path(self, case_id: str) -> Path:
        """Return a path where the <case>_metrics_deliverables.yaml file should be located."""
        return Path(self.root_dir, case_id, f"{case_id}_metrics_deliverables").with_suffix(
            FileExtensions.YAML
        )

    def get_params_file_path(self, case_id: str, params_file: Optional[Path] = None) -> Path:
        """Return parameters file or a path where the default parameters file for a case id should be located."""
        if params_file:
            return Path(params_file).absolute()
        return Path((self.get_case_path(case_id)), f"{case_id}_params_file").with_suffix(
            FileExtensions.YAML
        )

    def create_case_directory(self, case_id: str, dry_run: bool = False) -> None:
        """Create case directory."""
        if not dry_run:
            Path(self.get_case_path(case_id=case_id)).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def extract_read_files(
        metadata: list, forward_read: bool = False, reverse_read: bool = False
    ) -> List[str]:
        """Extract a list of fastq file paths for either forward or reverse reads."""
        if forward_read and not reverse_read:
            read_direction = 1
        elif reverse_read and not forward_read:
            read_direction = 2
        else:
            raise ValueError("Either forward or reverse needs to be specified")
        sorted_metadata: list = sorted(metadata, key=operator.itemgetter("path"))
        return [d["path"] for d in sorted_metadata if d["read"] == read_direction]

    def verify_case_config_file_exists(self, case_id: str, dry_run: bool = False) -> None:
        """Raise an error if config file is not found."""
        if not dry_run and not Path(self.get_case_config_path(case_id=case_id)).exists():
            raise ValueError(f"No config file found for case {case_id}")

    def verify_deliverables_file_exists(self, case_id: str) -> None:
        """Raise an error if deliverables files file is not found."""
        if not Path(self.get_deliverables_file_path(case_id=case_id)).exists():
            raise CgError(f"No deliverables file found for case {case_id}")

    def get_replace_map(self, case_id: str) -> dict:
        """Get a mapping to replace constants from template to create case deliverables."""
        return {
            "PATHTOCASE": str(self.get_case_path(case_id)),
            "CASEID": case_id,
        }

    @staticmethod
    def get_template_deliverables_file_content(file_bundle_template: Path) -> dict:
        """Return deliverables file template content."""
        return ReadFile.get_content_from_file(
            file_format=FileFormat.YAML,
            file_path=file_bundle_template,
        )

    @staticmethod
    def add_bundle_header(deliverables_content: dict) -> dict:
        """Adds header to bundle content."""
        return {"files": deliverables_content}

    @staticmethod
    def write_deliverables_bundle(
        deliverables_content: dict, file_path: Path, file_format=FileFormat.YAML
    ) -> None:
        """Write deliverables file."""
        WriteFile.write_file_from_content(
            content=deliverables_content, file_format=file_format, file_path=file_path
        )

    def write_trailblazer_config(self, case_id: str, tower_id: str) -> None:
        """Write Tower IDs to a file used as the Trailblazer config."""
        config_path: Path = self.get_trailblazer_config_path(case_id=case_id)
        LOG.info(f"Writing Tower ID to {config_path.as_posix()}")
        WriteFile.write_file_from_content(
            content={case_id: [tower_id]},
            file_format=FileFormat.YAML,
            file_path=config_path,
        )

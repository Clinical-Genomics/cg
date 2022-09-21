"""Module for Nextflow Analysis API."""

import logging
from pathlib import Path
from datetime import datetime
import os
import operator
from cg.constants.constants import (
    NFX_WORK_DIR,
)

LOG = logging.getLogger(__name__)


class NextflowAnalysisAPI:
    """Handles communication between nextflow processes
    and the rest of CG infrastructure."""

    @classmethod
    def get_case_path(cls, case_id: str, root_dir: str) -> Path:
        """Returns a path where the rnafusion case should be located."""
        return Path(root_dir, case_id)

    @classmethod
    def verify_case_config_file_exists(cls, case_id: str, root_dir: str) -> None:
        if not Path(cls.get_case_config_path(case_id=case_id, root_dir=root_dir)).exists():
            raise ValueError(f"No config file found for case {case_id}")

    @classmethod
    def get_case_config_path(cls, case_id: str, root_dir: str) -> Path:
        """Generates a path where the Rnafusion sample sheet for the case_id should be located."""
        return Path((cls.get_case_path(case_id, root_dir)), case_id + "_samplesheet.csv")

    @classmethod
    def make_case_folder(cls, case_id: str, root_dir: str) -> None:
        """Make the case folder where analysis should be located."""
        os.makedirs(cls.get_case_path(case_id, root_dir), exist_ok=True)

    @classmethod
    def extract_read_files(cls, read_nb: int, metadata: list) -> list:
        sorted_metadata: list = sorted(metadata, key=operator.itemgetter("path"))
        return [d["path"] for d in sorted_metadata if d["read"] == read_nb]

    @classmethod
    def get_log_path(cls, case_id: str, root_dir: str, pipeline: str, log: Path = None) -> Path:
        if log:
            return log
        launch_time: str = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
        return Path(
            cls.get_case_path(case_id, root_dir),
            case_id + "_" + pipeline + "_nextflow_log_" + launch_time + ".log",
        )

    @classmethod
    def get_workdir_path(cls, case_id: str, root_dir: str, work_dir: Path = None) -> Path:
        if work_dir:
            return work_dir
        return Path(cls.get_case_path(case_id, root_dir), NFX_WORK_DIR)

    @classmethod
    def get_input_path(cls, case_id: str, root_dir: str, input: Path = None) -> Path:
        if input:
            return input
        return Path(cls.get_case_config_path(case_id, root_dir))

    @classmethod
    def get_outdir_path(cls, case_id: str, root_dir: str, outdir: Path = None) -> Path:
        if outdir:
            return outdir
        return Path(cls.get_case_path(case_id, root_dir))

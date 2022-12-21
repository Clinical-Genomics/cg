"""Module for Gens API."""

import logging
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict

from cg.constants.constants import FileFormat
from cg.exc import CaseNotFoundError
from cg.io.controller import ReadStream
from cg.utils import Process
from cg.utils.dict import get_list_from_dictionary

LOG = logging.getLogger(__name__)


class GensAPI:
    """API for Gens."""

    def __init__(self, binary_path: str, config_path: str):
        self.binary_path = binary_path
        self.config_path = config_path
        self.process = Process(binary=self.binary_path, config=self.config_path)

    def load(
        self,
        sample_id: str,
        genome_build: str,
        baf_path: Path,
        coverage_path: Path,
        case_id: str,
    ) -> None:
        """Load Gens sample file paths into database."""
        load_params = {
            "--sample-id": sample_id,
            "--genome-build": genome_build,
            "--baf": baf_path.as_posix(),
            "--coverage": coverage_path.as_posix(),
            "--case-id": case_id,
        }
        load_call_params: list = ["load", "sample"] + get_list_from_dictionary(load_params)
        self.process.run_command(parameters=load_call_params)

    def __repr__(self):
        return f"GensAPI(binary_path={Path(self.binary_path).stem}, config_path={Path(self.config_path).stem})"

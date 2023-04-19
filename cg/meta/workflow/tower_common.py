"""Module for Tower Analysis API."""

import logging
from pathlib import Path
from typing import Iterable, List

from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile
from cg.utils.utils import build_command_from_dict

LOG = logging.getLogger(__name__)


class TowerAnalysisAPI:
    """Handles communication between tower processes
    and the rest of CG infrastructure."""

    @classmethod
    def get_tower_launch_parameters(cls, tower_pipeline: str, command_args: dict) -> List[str]:
        """Returns a tower launch command given a dictionary with arguments."""

        tower_options: List[str] = build_command_from_dict(
            options={
                f"--{arg}": command_args.get(arg, None)
                for arg in (
                    "work-dir",
                    "profile",
                    "params-file",
                    "config",
                    "name",
                    "revision",
                    "compute-env",
                )
            },
            exclude_true=True,
        )
        return ["launch"] + tower_options + [tower_pipeline]

    @staticmethod
    def get_tower_id(stdout_lines: Iterable) -> str:
        """Parse the stdout and return a workflow id. An example of the output to parse is:
        Case <CASE_ID> exists in status db
        Running RNAFUSION analysis for <CASE_ID>
        Pipeline will be executed using tower
        Running command <COMMAND>

          Workflow 1uxZE9JM7Tl58r submitted at [<WORKSPACE>] workspace.

        https://<URL_TO_TOWER_CASE>
        Action running set for case <CASE_ID>"""
        for line in stdout_lines:
            if line.strip().startswith("Workflow"):
                return line.strip().split()[1]

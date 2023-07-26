"""Module for Tower Analysis API."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
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
                f"--{arg.replace('_', '-')}": command_args.get(arg, None)
                for arg in (
                    "work_dir",
                    "profile",
                    "params_file",
                    "config",
                    "name",
                    "revision",
                    "compute_env",
                )
            },
            exclude_true=True,
        )
        return ["launch"] + tower_options + [tower_pipeline]

    @classmethod
    def get_tower_relaunch_parameters(cls, from_tower_id: int, command_args: dict) -> List[str]:
        """Returns a tower relaunch command given a dictionary with arguments."""

        tower_options: List[str] = build_command_from_dict(
            options={
                f"--{arg.replace('_', '-')}": command_args.get(arg, None)
                for arg in (
                    "profile",
                    "params_file",
                    "config",
                    "compute_env",
                )
            },
            exclude_true=True,
        )
        now: str = datetime.now().strftime("%Y%m%d%H%M%S")
        return [
            "runs",
            "relaunch",
            "--id",
            str(from_tower_id),
            "--name",
            f"{command_args.get('name')}_from{str(from_tower_id)}_{now}",
        ] + tower_options

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

    @classmethod
    def get_last_tower_id(cls, case_id: str, trailblazer_config: Path) -> int:
        """Return the previously-stored NF-Tower ID."""
        if not trailblazer_config.exists():
            raise FileNotFoundError(f"No NF-Tower ID found for case {case_id}.")
        return ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=trailblazer_config
        ).get(case_id)[-1]

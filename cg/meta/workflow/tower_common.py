"""Module for Tower Analysis API."""

import logging
from typing import List

from cg.utils.utils import build_command_from_dict

LOG = logging.getLogger(__name__)


class TowerAnalysisAPI:
    """Handles communication between tower processes
    and the rest of CG infrastructure."""

    @classmethod
    def get_tower_launch_parameters(cls, tower_pipeline: str, command_args: dict) -> List[str]:
        """Returns a tower launch command given a dictionary with arguments."""

        tower_options: List[str] = build_command_from_dict(
            options=dict(
                (f"--{arg}", command_args.get(arg, None))
                for arg in (
                    "work-dir",
                    "profile",
                    "params-file",
                    "config",
                    "name",
                    "revision",
                    "compute-env",
                )
            ),
            exclude_true=True,
        )
        parameters = ["launch"] + tower_options + [tower_pipeline]
        return parameters

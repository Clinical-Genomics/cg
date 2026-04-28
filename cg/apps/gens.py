"""Module for Gens API."""

import logging
import subprocess
from os import environ

from cg.constants.process import EXIT_SUCCESS
from cg.utils.dict import get_list_from_dictionary

LOG = logging.getLogger(__name__)


class GensAPI:
    """API for Gens."""

    def __init__(self, config):
        self.binary_path: str = config.binary_path
        self.config_path: str = config.config_path
        self.shell_env = self._get_shell_env()
        self.dry_run: bool = False

    def _get_shell_env(self):
        shell_vars = environ.copy()
        shell_vars.update({"CONFIG_FILE": self.config_path})
        return shell_vars

    def set_dry_run(self, dry_run: bool) -> None:
        """Set the dry run state."""
        self.dry_run = dry_run

    def load(
        self,
        baf_path: str,
        case_id: str,
        coverage_path: str,
        genome_build: str,
        sample_id: str,
    ) -> int:
        """Load Gens sample file paths into database."""
        args: list[str] = [self.binary_path, "load", "sample", "--force"]
        kw_args: dict[str, str] = {
            "--sample-id": sample_id,
            "--genome-build": genome_build,
            "--baf": baf_path,
            "--coverage": coverage_path,
            "--case-id": case_id,
        }
        command: list[str] = args + get_list_from_dictionary(kw_args)

        if self.dry_run:
            LOG.info(f"Dry run: process call '{command}' will not be executed!!")
            return EXIT_SUCCESS
        else:
            res = subprocess.run(
                args=command,
                check=False,
                env=self.shell_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if res.returncode != EXIT_SUCCESS:
                LOG.info(res.stdout.decode("utf-8").rstrip())
                LOG.critical(f"Call '{command}' exit with a non zero exit code")
                LOG.critical(res.stderr.decode("utf-8").rstrip())
                raise subprocess.CalledProcessError(res.returncode, command)

            return res.returncode

    def __str__(self):
        return f"GensAPI(dry_run: {self.dry_run})"

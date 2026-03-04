"""Interactions with the genotype tool"""

import logging

from cg.utils.commands import Process

LOG = logging.getLogger(__name__)


class GenotypeAPI:
    """Interface with Genotype app.

    The config should contain a 'genotype' key:

        { 'database': 'mysql://localhost:3306/database' }
    """

    def __init__(self, config: dict):
        self.process = Process(
            binary=config["genotype"]["binary_path"], config=config["genotype"]["config_path"]
        )
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Set the dry run state"""
        self.dry_run = dry_run

    def __str__(self):
        return f"GenotypeAPI(dry_run: {self.dry_run})"

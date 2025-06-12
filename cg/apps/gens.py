"""Module for Gens API."""

import logging

from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.store.models import Case
from cg.utils import Process
from cg.utils.dict import get_list_from_dictionary

LOG = logging.getLogger(__name__)


class GensAPI:
    """API for Gens."""

    def __init__(self, config: dict[str, dict[str, str]]):
        self.binary_path: str = config["gens"]["binary_path"]
        self.config_path: str = config["gens"]["config_path"]
        self.process: Process = Process(
            binary=self.binary_path, config=self.config_path, config_parameter="--env-file"
        )
        self.dry_run: bool = False

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
    ) -> None:
        """Load Gens sample file paths into database."""
        load_params: dict[str, str] = {
            "--sample-id": sample_id,
            "--genome-build": genome_build,
            "--baf": baf_path,
            "--coverage": coverage_path,
            "--case-id": case_id,
        }
        load_call_params: list[str] = ["load", "sample", "--force"]
        load_call_params += get_list_from_dictionary(load_params)
        self.process.run_command(parameters=load_call_params, dry_run=self.dry_run)
        if self.process.stderr:
            LOG.warning(self.process.stderr)

    @staticmethod
    def is_suitable_for_upload(case: Case) -> bool:
        """Check if a cancer case supports Gens upload."""
        return all(
            sample.prep_category == SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
            for sample in case.samples
        )

    def __str__(self):
        return f"GensAPI(dry_run: {self.dry_run})"

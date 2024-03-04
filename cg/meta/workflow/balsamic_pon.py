"""Module for Balsamic PON Analysis API."""

import logging
from pathlib import Path

from cg.constants.constants import Workflow
from cg.exc import BalsamicStartError
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from cg.utils.utils import build_command_from_dict

LOG = logging.getLogger(__name__)


class BalsamicPonAnalysisAPI(BalsamicAnalysisAPI):
    """Handles communication between Balsamic PON processes and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.BALSAMIC_PON,
    ):
        super().__init__(config=config, workflow=workflow)

    def config_case(
        self,
        case_id: str,
        gender: str,
        genome_version: str,
        panel_bed: str,
        pon_cnn: str,
        observations: list[str],
        cache_version: str,
        dry_run: bool = False,
    ) -> None:
        """Creates a config file for BALSAMIC PON analysis."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_parameters: dict = self.get_sample_params(case_id=case_id, panel_bed=panel_bed)
        if not sample_parameters:
            LOG.error(f"{case_id} has no samples tagged for Balsamic PON analysis")
            raise BalsamicStartError()
        verified_panel_bed: str = self.get_verified_bed(
            panel_bed=panel_bed, sample_data=sample_parameters
        )
        options: list[str] = build_command_from_dict(
            {
                "--case-id": case.internal_id,
                "--analysis-dir": self.root_dir,
                "--fastq-path": self.get_sample_fastq_destination_dir(case),
                "--panel-bed": verified_panel_bed,
                "--genome-version": genome_version,
                "--balsamic-cache": self.balsamic_cache,
                "--cache-version": cache_version,
                "--version": self.get_next_pon_version(verified_panel_bed),
            }
        )
        parameters: list[str] = ["config", "pon"] + options
        self.process.run_command(parameters=parameters, dry_run=dry_run)

    def get_case_config_path(self, case_id: str) -> Path:
        """Returns the BALSAMIC PON config path."""
        return Path(self.root_dir, case_id, case_id + "_PON.json")

    def get_next_pon_version(self, panel_bed: str) -> str:
        """Returns the next PON version to be generated."""
        latest_pon_file: str = self.get_latest_pon_file(panel_bed=panel_bed)
        next_version = int(Path(latest_pon_file).stem.split("_v")[-1]) + 1 if latest_pon_file else 1
        return "v" + str(next_version)

"""Module for Balsamic PON Analysis API"""

import logging
from pathlib import Path
from typing import List

from cg.constants.indexes import ListIndexes
from cg.exc import BalsamicStartError
from cgmodels.cg.constants import Pipeline

from cg.models.cg_config import CGConfig

from cg.meta.workflow.balsamic import BalsamicAnalysisAPI

LOG = logging.getLogger(__name__)


class BalsamicPonAnalysisAPI(BalsamicAnalysisAPI):
    """Handles communication between BALSAMIC processes and the rest of CG infrastructure"""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.BALSAMIC_PON,
    ):
        super().__init__(config=config, pipeline=pipeline)

    def config_case(
        self,
        case_id: str,
        gender: str,
        genome_version: str,
        panel_bed: str,
        pon_cnn: str,
        observations: List[str],
        dry_run: bool = False,
    ) -> None:
        """Creates a config file for BALSAMIC PON analysis"""

        case_obj = self.status_db.family(case_id)
        sample_data = self.get_sample_params(case_id=case_id, panel_bed=panel_bed)
        if len(sample_data) == 0:
            raise BalsamicStartError(f"{case_id} has no samples tagged for BALSAMIC PON analysis!")
        verified_panel_bed = self.get_verified_bed(panel_bed, sample_data)

        command = ["config", "pon"]
        options = BalsamicAnalysisAPI._BalsamicAnalysisAPI__build_command_str(
            {
                "--case-id": case_obj.internal_id,
                "--analysis-dir": self.root_dir,
                "--fastq-path": self.get_sample_fastq_destination_dir(case_obj),
                "--panel-bed": verified_panel_bed,
                "--genome-version": genome_version,
                "--balsamic-cache": self.balsamic_cache,
                "--version": self.get_next_pon_version(verified_panel_bed),
            }
        )

        parameters = command + options
        self.process.run_command(parameters=parameters, dry_run=dry_run)

    def get_case_config_path(self, case_id: str) -> Path:
        """Returns the BALSAMIC PON config path"""

        return Path(self.root_dir, case_id, case_id + "_PON.json")

    def get_next_pon_version(self, panel_bed: str) -> str:
        """Returns the next PON version to be generated"""

        latest_pon_file = self.get_latest_pon_file(panel_bed)
        next_version = (
            int(Path(latest_pon_file).stem.split("_v")[ListIndexes.LAST.value]) + 1
            if latest_pon_file
            else 1
        )

        return "v" + str(next_version)

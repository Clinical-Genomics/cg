"""Module for Balsamic PON Analysis API"""

import logging
from pathlib import Path
from typing import Optional

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
        dry_run: bool = False,
    ) -> None:
        """Creates a config file for BALSAMIC PON analysis"""

        case_obj = self.status_db.family(case_id)
        panel_bed = self.get_verified_bed(panel_bed)

        command = ["config", "pon"]
        options = BalsamicAnalysisAPI._BalsamicAnalysisAPI__build_command_str(
            {
                "--case-id": case_obj.internal_id,
                "--analysis-dir": self.root_dir,
                "--fastq-path": self.get_sample_fastq_destination_dir(case_obj),
                "--panel-bed": panel_bed,
                "--genome-version": genome_version,
                "--balsamic-cache": self.balsamic_cache,
                "--version": self.get_next_pon_version(panel_bed),
            }
        )

        parameters = command + options
        self.process.run_command(parameters=parameters, dry_run=dry_run)

    def get_verified_bed(self, panel_bed: Path, sample_data: dict = None) -> Optional[Path]:
        """Returns a valid capture bed path string"""

        if Path(panel_bed).is_file():
            return Path(panel_bed)
        else:
            derived_panel_bed = Path(
                self.bed_path,
                self.status_db.bed_version(panel_bed).filename,
            )
            if not derived_panel_bed.is_file():
                raise BalsamicStartError(
                    f"{panel_bed} or {derived_panel_bed} are not valid BED file paths. "
                    f"Please provide an absolute path to the desired BED file or a valid bed shortname."
                )
            return derived_panel_bed

    def get_next_pon_version(self, panel_bed: Path) -> str:
        """Returns the next PON version to be generated"""

        latest_pon_file = self.get_latest_pon_file(panel_bed)
        next_version = int(latest_pon_file.stem.split("_v")[-1]) + 1 if latest_pon_file else 1

        return "v" + str(next_version)

from pathlib import Path
from typing import Any

from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)


class NalloParamsFileCreator(ParamsFileCreator):
    def create(self, case_id: str, file_path: Path, sample_sheet_path: Path) -> Any:
        pass

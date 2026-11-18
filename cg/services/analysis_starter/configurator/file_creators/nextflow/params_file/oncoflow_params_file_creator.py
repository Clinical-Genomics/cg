from pathlib import Path
from typing import Any

from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)


class OncoflowParamsFileCreator(ParamsFileCreator):

    def create(self, case_id: str, file_path: Path, sample_sheet_path: Path) -> Any:
        """Create a params file for a single case."""
        pass

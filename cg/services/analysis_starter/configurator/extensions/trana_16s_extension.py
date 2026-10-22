from pathlib import Path

from cg.io.yaml import read_yaml
from cg.models.cg_config import TranaConfig
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)


class Trana16SExtension(PipelineExtension):
    def __init__(self, config: TranaConfig):
        self.config = config

    def configure(self, case_id: str, case_run_directory: Path) -> None:
        # create the case_deliverable file or pipeline_outputs
        # Get the template file
        read_yaml(Path(self.config.pipeline_deliverables))
        # Create a new file from the template file with CASEID, SAMPLEID and PATHTOCASE replaced, and VERSION set
        # Write the file to the case run directory

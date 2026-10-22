


from pathlib import Path

from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)


class Trana16SExtension(PipelineExtension):
    def configure(self, case_id: str, case_run_directory: Path) -> None:
        # create the case_deliverable file or pipeline_outputs
        
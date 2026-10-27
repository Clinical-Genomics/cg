from pathlib import Path

from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.case_deliverables_file_creator import (
    CaseDeliverablesFileCreator,
)


class TranaExtension(PipelineExtension):

    def __init__(self, case_deliverables_file_creator: CaseDeliverablesFileCreator):
        self.case_deliverables_file_creator = case_deliverables_file_creator

    def configure(self, case_id: str, case_run_directory: Path) -> None:
        pass

from pathlib import Path

from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.case_deliverables_file_creator import (
    CaseDeliverablesFileCreator,
)


class TranaExtension(PipelineExtension):

    def __init__(
        self,
        case_deliverables_file_creator: CaseDeliverablesFileCreator,
        trana_pipeline_deliverables: Path,
    ):
        self.case_deliverables_file_creator = case_deliverables_file_creator
        self.trana_pipeline_deliverables = trana_pipeline_deliverables

    def configure(self, case_id: str, case_run_directory: Path) -> None:
        self.case_deliverables_file_creator.create(
            case_id=case_id,
            file_path=self._get_case_deliverables_file_path(
                case_id=case_id, case_run_directory=case_run_directory
            ),
            pipeline_deliverables=self.trana_pipeline_deliverables,
        )

    @staticmethod
    def _get_case_deliverables_file_path(case_id: str, case_run_directory: Path) -> Path:
        return case_run_directory.joinpath(f"{case_id}_deliverables.yaml")

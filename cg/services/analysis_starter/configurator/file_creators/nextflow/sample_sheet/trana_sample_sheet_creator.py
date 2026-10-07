from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowFastqSampleSheetCreator,
)

HEADERS: list[str] = ["sample", "fastq_1", "fastq_2", "control"]


class TranaSampleSheetCreator(NextflowFastqSampleSheetCreator):

    def _get_content(self, case_id: str) -> list[list[str]]:
        return []

    def _get_sample_sheet_content_per_sample(self):
        pass

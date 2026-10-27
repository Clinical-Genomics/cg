from cg.constants.housekeeper_tags import SequencingFileTag
from cg.exc import (
    MissingNegativeControlError,
    MultipleNegativeControlsError,
    SampleSheetContentError,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowFastqSampleSheetCreator,
)
from cg.store.models import Case, Sample

HEADERS: list[str] = ["sample", "fastq_1", "fastq_2", "neg_control"]


class TranaSampleSheetCreator(NextflowFastqSampleSheetCreator):

    def _get_content(self, case_id: str) -> list[list[str]]:

        case: Case = self.store.get_case_by_internal_id_strict(internal_id=case_id)
        sample_sheet_content: list[list[str]] = [HEADERS]
        sample_control: Sample = self._get_case_negative_control(case)
        for sample in case.samples:
            sample_sheet_content.extend(
                self._get_sample_sheet_content_per_sample(sample=sample, control=sample_control)
            )
        if sample_sheet_content == [HEADERS]:
            raise SampleSheetContentError(f"Sample sheet for case {case_id} is empty.")
        return sample_sheet_content

    def _get_sample_sheet_content_per_sample(
        self, sample: Sample, control: Sample
    ) -> list[list[str]]:
        content: list[list[str]] = []
        fastq_files: list[str] = self._get_fastq_paths(sample)
        for fastq in fastq_files:
            entry: list[str] = [sample.name, fastq, "", control.name if sample != control else ""]
            content.append(entry)
        return content

    def _get_fastq_paths(self, sample) -> list[str]:
        fastq_files: list[str] = [
            file.full_path
            for file in self.housekeeper_api.files(
                bundle=sample.internal_id, tags={SequencingFileTag.FASTQ}
            ).all()
        ]
        return fastq_files

    @staticmethod
    def _get_case_negative_control(case: Case) -> Sample:
        negative_controls: list[Sample] = [
            sample for sample in case.samples if sample.is_negative_control
        ]
        if len(negative_controls) == 0:
            raise MissingNegativeControlError(
                f"No negative control found in case {case.internal_id}."
            )
        elif len(negative_controls) > 1:
            raise MultipleNegativeControlsError(
                f"Multiple controls {[control.internal_id for control in negative_controls]} found in case {case.internal_id}"
            )
        else:
            return negative_controls[0]

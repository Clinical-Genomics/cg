from pathlib import Path
from cg.apps.lims.api import LimsAPI
from cg.constants.constants import MutantQC
from cg.constants.lims import LimsProcess
from cg.exc import CgError
from cg.meta.workflow.mutant.quality_controller.metrics_parser_utils import parse_samples_results
from cg.meta.workflow.mutant.quality_controller.models import (
    MutantPoolSamples,
    SamplePoolAndResults,
    SampleQualityResults,
    CaseQualityResult,
    MutantQualityResult,
    ParsedSampleResults,
    SamplesQualityResults,
)
from cg.meta.workflow.mutant.quality_controller.report_generator_utils import (
    get_summary,
    write_report,
)
from cg.meta.workflow.mutant.quality_controller.result_logger_utils import (
    log_case_result,
    log_results,
    log_sample_result,
)
from cg.meta.workflow.mutant.quality_controller.utils import (
    has_external_negative_control_sample_valid_total_reads,
    has_internal_negative_control_sample_valid_total_reads,
    has_sample_valid_total_reads,
)
from cg.store.models import Case, Sample
from cg.store.store import Store


class MutantQualityController:
    def __init__(self, status_db: Store, lims: LimsAPI) -> None:
        self.status_db: Store = status_db
        self.lims: LimsAPI = lims

    def get_quality_control_result(
        self, case: Case, case_results_file_path: Path, case_qc_report_path: Path
    ) -> MutantQualityResult:
        """Perform QC check on a case and generate the QC_report."""
        sample_pool_and_results: SamplePoolAndResults = self._get_sample_pool_and_results(
            case_results_file_path=case_results_file_path,
            case=case,
        )

        samples_quality_results: SamplesQualityResults = self._get_samples_quality_results(
            sample_pool_and_results=sample_pool_and_results
        )
        case_quality_result: CaseQualityResult = self._get_case_quality_result(
            samples_quality_results
        )

        write_report(
            case_qc_report_path=case_qc_report_path,
            samples_quality_results=samples_quality_results,
            case_quality_result=case_quality_result,
        )

        log_results(
            case_quality_result=case_quality_result,
            samples_quality_results=samples_quality_results,
            report_file_path=case_qc_report_path,
        )

        summary: str = get_summary(
            case_quality_result=case_quality_result,
            samples_quality_results=samples_quality_results,
        )

        return MutantQualityResult(
            case_quality_result=case_quality_result,
            samples_quality_results=samples_quality_results,
            summary=summary,
        )

    def _get_samples_quality_results(
        self, sample_pool_and_results: SamplePoolAndResults
    ) -> SamplesQualityResults:
        samples_quality_results: list[SampleQualityResults] = []
        for sample in sample_pool_and_results.pool.samples:
            sample_results: ParsedSampleResults = sample_pool_and_results.results[
                sample.internal_id
            ]
            sample_quality_results: SampleQualityResults = (
                self._get_sample_quality_result_for_sample(
                    sample=sample, sample_results=sample_results
                )
            )
            samples_quality_results.append(sample_quality_results)

        internal_negative_control_sample: Sample = (
            sample_pool_and_results.pool.internal_negative_control
        )
        internal_negative_control_quality_metrics: SampleQualityResults = (
            self._get_sample_quality_result_for_internal_negative_control_sample(
                sample=internal_negative_control_sample
            )
        )

        external_negative_control_sample: Sample = (
            sample_pool_and_results.pool.external_negative_control
        )
        external_negative_control_sample_results: ParsedSampleResults = (
            sample_pool_and_results.results[external_negative_control_sample.internal_id]
        )
        external_negative_control_quality_metrics: SampleQualityResults = (
            self._get_sample_quality_result_for_external_negative_control_sample(
                sample=external_negative_control_sample,
                sample_results=external_negative_control_sample_results,
            )
        )

        return SamplesQualityResults(
            samples=samples_quality_results,
            internal_negative_control=internal_negative_control_quality_metrics,
            external_negative_control=external_negative_control_quality_metrics,
        )

    @staticmethod
    def _get_sample_quality_result_for_sample(
        sample: Sample, sample_results: ParsedSampleResults
    ) -> SampleQualityResults:
        does_sample_pass_reads_threshold: bool = has_sample_valid_total_reads(sample=sample)
        does_sample_pass_qc: bool = does_sample_pass_reads_threshold and sample_results.passes_qc
        sample_quality_result = SampleQualityResults(
            sample_id=sample.internal_id,
            passes_qc=does_sample_pass_qc,
            passes_reads_threshold=does_sample_pass_reads_threshold,
            passes_mutant_qc=sample_results.passes_qc,
        )

        log_sample_result(
            result=sample_quality_result,
        )
        return sample_quality_result

    @staticmethod
    def _get_sample_quality_result_for_internal_negative_control_sample(
        sample: Sample,
    ) -> SampleQualityResults:
        does_sample_pass_reads_threshold: bool = (
            has_internal_negative_control_sample_valid_total_reads(sample=sample)
        )
        sample_quality_result = SampleQualityResults(
            sample_id=sample.internal_id,
            passes_qc=does_sample_pass_reads_threshold,
            passes_reads_threshold=does_sample_pass_reads_threshold,
        )

        log_sample_result(result=sample_quality_result, is_external_negative_control=True)
        return sample_quality_result

    @staticmethod
    def _get_sample_quality_result_for_external_negative_control_sample(
        sample: Sample, sample_results: ParsedSampleResults
    ) -> SampleQualityResults:
        does_sample_pass_reads_threshold: bool = (
            has_external_negative_control_sample_valid_total_reads(sample=sample)
        )
        sample_passes_qc: bool = does_sample_pass_reads_threshold and not sample_results.passes_qc
        sample_quality_result = SampleQualityResults(
            sample_id=sample.internal_id,
            passes_qc=sample_passes_qc,
            passes_reads_threshold=does_sample_pass_reads_threshold,
            passes_mutant_qc=sample_results.passes_qc,
        )

        log_sample_result(result=sample_quality_result, is_external_negative_control=True)
        return sample_quality_result

    def _get_case_quality_result(
        self, samples_quality_results: SamplesQualityResults
    ) -> CaseQualityResult:
        external_negative_control_pass_qc: bool = (
            samples_quality_results.external_negative_control.passes_qc
        )
        internal_negative_control_pass_qc: bool = (
            samples_quality_results.internal_negative_control.passes_qc
        )

        samples_pass_qc: bool = self._samples_pass_qc(
            samples_quality_results=samples_quality_results
        )

        case_passes_qc: bool = (
            samples_pass_qc
            and internal_negative_control_pass_qc
            and external_negative_control_pass_qc
        )

        result = CaseQualityResult(
            passes_qc=case_passes_qc,
            internal_negative_control_passes_qc=internal_negative_control_pass_qc,
            external_negative_control_passes_qc=external_negative_control_pass_qc,
            fraction_samples_passes_qc=samples_pass_qc,
        )

        log_case_result(result)
        return result

    @staticmethod
    def _samples_pass_qc(samples_quality_results: SamplesQualityResults) -> bool:
        fraction_failed_samples: float = (
            samples_quality_results.failed_samples_count
            / samples_quality_results.total_samples_count
        )
        return fraction_failed_samples < MutantQC.FRACTION_OF_SAMPLES_WITH_FAILED_QC_THRESHOLD

    def _get_internal_negative_control_id_for_case(self, case: Case) -> str:
        """Query lims to retrive internal_negative_control_id for a mutant case sequenced in one pool."""

        sample_internal_id = case.sample_ids[0]
        internal_negative_control_id: str = (
            self.lims.get_internal_negative_control_id_from_sample_in_pool(
                sample_internal_id=sample_internal_id, pooling_step=LimsProcess.COVID_POOLING_STEP
            )
        )
        return internal_negative_control_id

    def _get_internal_negative_control_sample_for_case(
        self,
        case: Case,
    ) -> Sample:
        internal_negative_control_id: str = self._get_internal_negative_control_id_for_case(
            case=case
        )
        return self.status_db.get_sample_by_internal_id(internal_id=internal_negative_control_id)

    def _get_mutant_pool_samples(self, case: Case) -> MutantPoolSamples:
        samples = []
        external_negative_control = None

        for sample in case.samples:
            if sample.is_negative_control:
                external_negative_control = sample
                continue
            samples.append(sample)

        if not external_negative_control:
            raise CgError(f"No external negative control sample found for case {case.internal_id}.")

        internal_negative_control: Sample = self._get_internal_negative_control_sample_for_case(
            case=case
        )

        return MutantPoolSamples(
            samples=samples,
            external_negative_control=external_negative_control,
            internal_negative_control=internal_negative_control,
        )

    def _get_sample_pool_and_results(
        self, case_results_file_path: Path, case: Case
    ) -> SamplePoolAndResults:
        try:
            samples: MutantPoolSamples = self._get_mutant_pool_samples(case=case)
        except Exception as exception_object:
            raise CgError(
                f"Not possible to retrieve samples for case {case.internal_id}: {exception_object}"
            ) from exception_object

        try:
            samples_results: dict[str, ParsedSampleResults] = parse_samples_results(
                case=case, results_file_path=case_results_file_path
            )
        except Exception as exception_object:
            raise CgError(
                f"Not possible to retrieve results for case {case.internal_id}: {exception_object}"
            )

        return SamplePoolAndResults(pool=samples, results=samples_results)

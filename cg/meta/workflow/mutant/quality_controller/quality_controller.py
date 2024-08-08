from pathlib import Path
from cg.apps.lims.api import LimsAPI
from cg.constants.constants import MutantQC
from cg.constants.lims import LimsProcess
from cg.exc import CgError
from cg.meta.workflow.mutant.quality_controller.metrics_parser_utils import parse_samples_results
from cg.meta.workflow.mutant.quality_controller.models import (
    MutantPoolSamples,
    QualityMetrics,
    SampleQualityResults,
    CaseQualityResult,
    QualityResult,
    SampleResults,
    SamplesQualityResults,
)
from cg.meta.workflow.mutant.quality_controller.report_generator_utils import (
    get_report_path,
    get_summary,
    write_report,
)
from cg.meta.workflow.mutant.quality_controller.result_logger_utils import (
    log_case_result,
    log_results,
    log_sample_result,
)
from cg.meta.workflow.mutant.quality_controller.utils import (
    get_quality_metrics,
    has_valid_total_reads,
)
from cg.store.models import Case, Sample
from cg.store.store import Store


class MutantQualityController:
    def __init__(self, status_db: Store, lims: LimsAPI) -> None:
        self.status_db: Store = status_db
        self.lims: LimsAPI = lims

    def get_quality_control_result(
        self, case: Case, case_path: Path, case_results_file_path: Path
    ) -> QualityResult:
        """Perform QC check on a case and generate the QC_report."""
        quality_metrics: QualityMetrics = get_quality_metrics(
            case_results_file_path=case_results_file_path,
            case=case,
            status_db=self.status_db,
            lims=self.lims,
        )

        samples_quality_results: SamplesQualityResults = self._get_samples_quality_results(
            quality_metrics=quality_metrics
        )
        case_quality_result: CaseQualityResult = self._get_case_quality_result(
            samples_quality_results
        )

        write_report(
            case_path=case_path,
            samples_quality_results=samples_quality_results,
            case_quality_result=case_quality_result,
        )

        report_file_path = get_report_path(case_path=case_path)

        log_results(
            case_quality_result=case_quality_result,
            samples_quality_results=samples_quality_results,
            report_file_path=report_file_path,
        )

        summary: str = get_summary(
            case_quality_result=case_quality_result,
            samples_quality_results=samples_quality_results,
            report_file_path=report_file_path,
        )

        return QualityResult(
            case_quality_result=case_quality_result,
            samples_quality_results=samples_quality_results,
            summary=summary,
        )

    def _get_samples_quality_results(
        self, quality_metrics: QualityMetrics
    ) -> SamplesQualityResults:
        samples_quality_results: list[SampleQualityResults] = []
        for sample in quality_metrics.pool.samples:
            sample_results: SampleResults = quality_metrics.results[sample.internal_id]
            sample_quality_results: SampleQualityResults = self._get_sample_quality_results(
                sample=sample, sample_results=sample_results
            )
            samples_quality_results.append(sample_quality_results)

        internal_negative_control_sample: Sample = quality_metrics.pool.internal_negative_control
        internal_negative_control_quality_metrics: SampleQualityResults = (
            self._get_sample_quality_results(
                sample=internal_negative_control_sample, internal_negative_control=True
            )
        )

        external_negative_control_sample: Sample = quality_metrics.pool.external_negative_control
        external_negative_control_sample_results: SampleResults = quality_metrics.results[
            external_negative_control_sample.internal_id
        ]
        external_negative_control_quality_metrics: SampleQualityResults = (
            self._get_sample_quality_results(
                sample=external_negative_control_sample,
                sample_results=external_negative_control_sample_results,
                external_negative_control=True,
            )
        )

        return SamplesQualityResults(
            samples=samples_quality_results,
            internal_negative_control=internal_negative_control_quality_metrics,
            external_negative_control=external_negative_control_quality_metrics,
        )

    @staticmethod
    def _get_sample_quality_results(
        sample: Sample,
        sample_results: SampleResults | None = None,
        external_negative_control: bool = False,
        internal_negative_control: bool = False,
    ) -> SampleQualityResults:
        sample_has_valid_total_reads: bool = has_valid_total_reads(
            sample=sample,
            external_negative_control=external_negative_control,
            internal_negative_control=internal_negative_control,
        )

        if internal_negative_control:
            sample_quality = SampleQualityResults(
                sample_id=sample.internal_id,
                passes_qc=sample_has_valid_total_reads,
                passes_reads_threshold=sample_has_valid_total_reads,
            )
        else:
            if external_negative_control:
                sample_passes_qc: bool = sample_has_valid_total_reads and not sample_results.qc_pass
            else:
                sample_passes_qc: bool = sample_has_valid_total_reads and sample_results.qc_pass

            sample_quality = SampleQualityResults(
                sample_id=sample.internal_id,
                passes_qc=sample_passes_qc,
                passes_reads_threshold=sample_has_valid_total_reads,
                passes_mutant_qc=sample_results.qc_pass,
            )

        log_sample_result(
            result=sample_quality,
            external_negative_control=external_negative_control,
            internal_negative_control=internal_negative_control,
        )
        return sample_quality

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

        result = CaseQualityResult(
            passes_qc=(
                samples_pass_qc
                and internal_negative_control_pass_qc
                and external_negative_control_pass_qc
            ),
            internal_negative_control_passes_qc=internal_negative_control_pass_qc,
            external_negative_control_passes_qc=external_negative_control_pass_qc,
            samples_pass_qc=samples_pass_qc,
        )
        log_case_result(result)
        return result

    @staticmethod
    def _samples_pass_qc(samples_quality_results: SamplesQualityResults) -> bool:
        return (
            samples_quality_results.failed_samples_count
            / samples_quality_results.total_samples_count
            < MutantQC.FRACTION_OF_SAMPLES_WITH_FAILED_QC_TRESHOLD
        )

    def get_internal_negative_control_id_for_case(self, case: Case) -> str:
        """Query lims to retrive internal_negative_control_id for a mutant case sequenced in one pool."""

        sample_internal_id = case.sample_ids[0]
        internal_negative_control_id: str = (
            self.lims.get_internal_negative_control_id_from_sample_in_pool(
                sample_internal_id=sample_internal_id, pooling_step=LimsProcess.COVID_POOLING_STEP
            )
        )
        return internal_negative_control_id

    def get_internal_negative_control_sample_for_case(
        self,
        case: Case,
    ) -> Sample:
        internal_negative_control_id: str = self.get_internal_negative_control_id_for_case(
            lims=self.lims, case=case
        )
        return self.status_db.get_sample_by_internal_id(internal_id=internal_negative_control_id)

    def get_mutant_pool_samples(self, case: Case) -> MutantPoolSamples:
        samples = []
        external_negative_control = None

        for sample in case.samples:
            if sample.is_negative_control:
                external_negative_control = sample
                continue
            samples.append(sample)

        if not external_negative_control:
            raise CgError(f"No external negative control sample found for case {case}.")

        internal_negative_control: Sample = self.get_internal_negative_control_sample_for_case(
            case=case
        )

        return MutantPoolSamples(
            samples=samples,
            external_negative_control=external_negative_control,
            internal_negative_control=internal_negative_control,
        )

    def get_quality_metrics(self, case_results_file_path: Path, case: Case) -> QualityMetrics:
        try:
            samples_results: dict[str, SampleResults] = parse_samples_results(
                case=case, results_file_path=case_results_file_path
            )
        except Exception as exception_object:
            raise CgError(
                f"Not possible to retrieve results for case {case}."
            ) from exception_object

        try:
            samples: MutantPoolSamples = self.get_mutant_pool_samples(case=case)
        except Exception as exception_object:
            raise CgError(
                f"Not possible to retrieve samples for case {case}."
            ) from exception_object

        return QualityMetrics(results=samples_results, pool=samples)

from cg.meta.workflow.mutant.quality_controller import QualityController
from cg.meta.workflow.mutant.quality_controller.utils import get_quality_metrics


def test_quality_control(mutant_store, mutant_lims, passing_report_path):
    # GIVEN a case object and a corresponding case_results_file_path
    mutant_case_qc_pass = mutant_store.get_case_by_internal_id("mutant_case_qc_pass")
    # WHEN performing qc
    QualityController(status_db=mutant_store, lims=mutant_lims).quality_control(
        case=mutant_case_qc_pass,
        case_path="",
        case_results_file_path=passing_report_path,
    )

    # THEN no error is thrown


#     def quality_control(
#         self, case: Case, case_path: Path, case_results_file_path: Path
#     ) -> QualityResult | None:
#         """Perform QC check on a case and generate the QC_report."""
#         quality_metrics: QualityMetrics = get_quality_metrics(
#             case_results_file_path, case, self.status_db, self.lims
#         )
#         if not quality_metrics:
#             return None
#         else:
#             sample_results: list[SampleQualityResult] = self.quality_control_samples(
#                 quality_metrics
#             )
#             case_result: CaseQualityResult = self.quality_control_case(sample_results)

#             report_file: Path = get_report_path(case_path=case_path)
#             ReportGenerator.report(out_file=report_file, samples=sample_results, case=case_result)
#             ResultLogger.log_results(case=case_result, samples=sample_results, report=report_file)
#             summary: str = ReportGenerator.get_summary(
#                 case=case_result, samples=sample_results, report_path=report_file
#             )
#             return QualityResult(case=case_result, samples=sample_results, summary=summary)


#     def quality_control_samples(self, quality_metrics: QualityMetrics) -> list[SampleQualityResult]:
#         sample_results: list[SampleQualityResult] = []

#         for sample_id in quality_metrics.sample_id_list:
#             result = self.quality_control_sample(sample_id, quality_metrics)
#             sample_results.append(result)

#         return sample_results


def test_quality_control_samples(mutant_store, mutant_lims, passing_report_path):
    # GIVEN a case object
    mutant_case_qc_pass = mutant_store.get_case_by_internal_id("mutant_case_qc_pass")
    quality_metrics = get_quality_metrics(
        passing_report_path,
        mutant_case_qc_pass,
        mutant_store,
        mutant_lims,
    )

    # WHEN performing qc on samples
    QualityController(status_db=mutant_store, lims=mutant_lims).quality_control_samples(
        quality_metrics=quality_metrics
    )

    # THEN no error is thrown


#     def quality_control_case(self, sample_results: list[SampleQualityResult]) -> CaseQualityResult:
#         internal_negative_control_pass_qc: bool = internal_negative_control_qc_pass(sample_results)
#         external_negative_control_pass_qc: bool = external_negative_control_qc_pass(sample_results)

#         case_pass_qc: bool = self.case_qc_pass(sample_results=sample_results)

#         result = CaseQualityResult(
#             passes_qc=(
#                 case_pass_qc
#                 and internal_negative_control_pass_qc
#                 and external_negative_control_pass_qc
#             ),
#             internal_negative_control_pass_qc=internal_negative_control_pass_qc,
#             external_negative_control_pass_qc=external_negative_control_pass_qc,
#         )
#         ResultLogger.log_case_result(result)
#         return result

#     def case_qc_pass(sample_results: list[SampleQualityResult]) -> bool:
#         total_samples: int = 0
#         failed_samples: int = 0

#         for sample_result in sample_results:
#             if (
#                 not sample_result.is_external_negative_control
#                 and not sample_result.is_internal_negative_control
#             ):
#                 total_samples += 1
#                 if not sample_result.passes_qc:
#                     failed_samples += 1

#         return failed_samples / total_samples > MutantQC.FRACTION_OF_SAMPLES_WITH_FAILED_QC_TRESHOLD

import logging
from pathlib import Path

from cg.io.json import read_json, write_json

from cg.constants.constants import MicrosaltAppTags, MicrosaltQC
from cg.meta.workflow.microsalt.models import QualityMetrics, QualityResult, SampleMetrics
from cg.meta.workflow.microsalt.utils import (
    is_valid_duplication_rate,
    is_valid_mapped_rate,
    is_valid_median_insert_size,
    is_valid_total_reads,
    is_valid_total_reads_for_control,
    parse_quality_metrics,
)
from cg.models.orders.sample_base import ControlEnum
from cg.store.api.core import Store
from cg.store.models import Sample

LOG = logging.getLogger(__name__)


class QualityChecker:
    def __init__(self, status_db: Store):
        self.status_db = status_db

    def quality_control(self, run_dir_path: Path, lims_project: str):
        metrics_file_path: Path = Path(run_dir_path, f"{lims_project}.json")
        quality_metrics: QualityMetrics = parse_quality_metrics(metrics_file_path)

        sample_results: list[QualityResult] = []

        for sample_id, metrics in quality_metrics:
            result = self.quality_control_sample(sample_id=sample_id, metrics=metrics)
            sample_results.append(result)

        self.quality_control_case(sample_results)

    def quality_control_sample(self, sample_id: str, metrics: SampleMetrics) -> QualityResult:
        valid_reads: bool = self.is_valid_total_reads(sample_id)
        valid_mapped_rate: bool = self.is_valid_mapped_rate(metrics)
        valid_duplication_rate: bool = self.is_valid_duplication_rate(metrics)

    def quality_control_case(self, sample_results: list[QualityResult]) -> bool:
        pass

    def microsalt_qc(self, case_id: str, run_dir_path: Path, lims_project: str) -> bool:
        """Check if given microSALT case passes QC check."""
        failed_samples: dict = {}
        case_qc: dict = read_json(file_path=Path(run_dir_path, f"{lims_project}.json"))

        for sample_id in case_qc:
            sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)
            sample_check: dict | None = self.qc_sample_check(
                sample=sample,
                sample_qc=case_qc[sample_id],
            )
            if sample_check is not None:
                failed_samples[sample_id] = sample_check

        return self.qc_case_check(
            case_id=case_id,
            failed_samples=failed_samples,
            number_of_samples=len(case_qc),
            run_dir_path=run_dir_path,
        )

    def qc_case_check(
        self, case_id: str, failed_samples: dict, number_of_samples: int, run_dir_path: Path
    ) -> bool:
        """Perform the final QC check for a microbial case based on failed samples."""
        qc_pass: bool = True

        for sample_id in failed_samples:
            sample: Sample = self.status_db.get_sample_by_internal_id(internal_id=sample_id)
            if sample.control == ControlEnum.negative:
                qc_pass = False
            if sample.application_version.application.tag == MicrosaltAppTags.MWRNXTR003:
                qc_pass = False

        # Check if more than 10% of MWX samples failed
        if len(failed_samples) / number_of_samples > MicrosaltQC.QC_PERCENT_THRESHOLD_MWX:
            qc_pass = False

        if not qc_pass:
            LOG.warning(
                f"Case {case_id} failed QC, see {run_dir_path}/QC_done.json for more information."
            )
        else:
            LOG.info(f"Case {case_id} passed QC.")

        self.create_qc_done_file(
            run_dir_path=run_dir_path,
            failed_samples=failed_samples,
        )
        return qc_pass

    def create_qc_done_file(self, run_dir_path: Path, failed_samples: dict) -> None:
        """Creates a QC_done when a QC check is performed."""
        write_json(file_path=run_dir_path.joinpath("QC_done.json"), content=failed_samples)

    def qc_sample_check(self, sample: Sample, sample_qc: dict) -> dict | None:
        """Perform a QC on a sample."""
        if sample.control == ControlEnum.negative:
            reads_pass: bool = self.check_external_negative_control_sample(sample)
            if not reads_pass:
                LOG.warning(f"Negative control sample {sample.internal_id} failed QC.")
                return {"Passed QC Reads": reads_pass}
        else:
            reads_pass: bool = sample.sequencing_qc
            coverage_10x_pass: bool = self.check_coverage_10x(
                sample_name=sample.internal_id, sample_qc=sample_qc
            )
            if not reads_pass or not coverage_10x_pass:
                LOG.warning(f"Sample {sample.internal_id} failed QC.")
                return {"Passed QC Reads": reads_pass, "Passed Coverage 10X": coverage_10x_pass}

    def check_coverage_10x(self, sample_name: str, sample_qc: dict) -> bool:
        """Check if a sample passed the coverage_10x criteria."""
        try:
            return (
                sample_qc["microsalt_samtools_stats"]["coverage_10x"]
                >= MicrosaltQC.COVERAGE_10X_THRESHOLD
            )
        except TypeError as e:
            LOG.error(
                f"There is no 10X coverage value for sample {sample_name}, setting qc to fail for this sample"
            )
            LOG.error(f"See error: {e}")
            return False

    def check_external_negative_control_sample(self, sample: Sample) -> bool:
        """Check if external negative control passed read check"""
        return sample.reads < (
            sample.application_version.application.target_reads
            * MicrosaltQC.NEGATIVE_CONTROL_READS_THRESHOLD
        )

    def is_qc_required(self, case_run_dir: Path | None, case_id: str) -> bool:
        """Checks if a qc is required for a microbial case."""
        if case_run_dir is None:
            LOG.info(f"There are no running directories for case {case_id}.")
            return False

        if case_run_dir.joinpath("QC_done.json").exists():
            LOG.info(f"QC already performed for case {case_id}, storing case.")
            return False

        LOG.info(f"Performing QC on case {case_id}")
        return True

    def is_valid_total_reads(self, sample_id: str) -> bool:
        sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        target_reads: int = sample.application_version.application.target_reads
        sample_reads: int = sample.reads

        if sample.control == ControlEnum.negative:
            return is_valid_total_reads_for_control(
                sample_reads=sample_reads, target_reads=target_reads
            )
        return is_valid_total_reads(sample_reads=sample_reads, target_reads=target_reads)

    def is_valid_mapped_rate(self, metrics: SampleMetrics) -> bool:
        mapped_rate: float = metrics.microsalt_samtools_stats.mapped_rate
        return is_valid_mapped_rate(mapped_rate)

    def is_valid_duplication_rate(self, metrics: SampleMetrics) -> bool:
        duplication_rate: float = metrics.picard_markduplicate.duplication_rate
        return is_valid_duplication_rate(duplication_rate)

    def is_valid_median_insert_size(self, metrics: SampleMetrics) -> bool:
        insert_size: int = metrics.picard_markduplicate.insert_size
        return is_valid_median_insert_size(insert_size)

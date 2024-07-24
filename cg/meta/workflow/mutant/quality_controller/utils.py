from cg.apps.lims.api import LimsAPI
from cg.constants.constants import MutantQC
from cg.constants.lims import LimsArtifactTypes, LimsProcess
from cg.exc import CgError, LimsDataError
from cg.meta.workflow.mutant.constants import QUALITY_REPORT_FILE_NAME
from cg.meta.workflow.mutant.metrics_parser.metrics_parser import MetricsParser
from cg.meta.workflow.mutant.metrics_parser.models import SampleResults
from cg.meta.workflow.mutant.quality_controller.models import (
    MutantPoolSamples,
    QualityMetrics,
)
from genologics.entities import Artifact
from genologics.entities import Sample as LimsSample
from cg.models.cg_config import LOG
from cg.services.sequencing_qc_service.quality_checks.utils import sample_has_enough_reads
from cg.store.models import Case, Sample

from pathlib import Path

from cg.store.store import Store


def has_valid_total_reads(
    sample: Sample,
    external_negative_control: bool = False,
    internal_negative_control: bool = False,
) -> bool:
    if external_negative_control:
        return external_negative_control_sample_has_enough_reads(reads=sample.reads)

    if internal_negative_control:
        return internal_negative_control_sample_has_enough_reads(reads=sample.reads)

    return sample_has_enough_reads(sample=sample)


def external_negative_control_sample_has_enough_reads(reads: int) -> bool:
    return reads < MutantQC.EXTERNAL_NEGATIVE_CONTROL_READS_THRESHOLD


def internal_negative_control_sample_has_enough_reads(reads: int) -> bool:
    return reads < MutantQC.INTERNAL_NEGATIVE_CONTROL_READS_THRESHOLD


def get_negative_controls_from_list(samples: list[LimsSample]) -> list[LimsSample]:
    """Filter and return a list of internal negative controls from a given sample list."""
    negative_controls = []
    for sample in samples:
        if sample.udf.get("Control") == "negative" and sample.udf.get("customer") == "cust000":
            negative_controls.append(sample)
    return negative_controls


def get_internal_negative_control_id_from_lims(lims: LimsAPI, sample_internal_id: str) -> str:
    """Retrieve from lims the sample_id for the internal negative control sample present in the same pool as the given sample."""
    try:
        artifact: Artifact = lims.get_latest_artifact_for_sample(
            LimsProcess.COVID_POOLING_STEP, LimsArtifactTypes.ANALYTE, sample_internal_id
        )
        samples = artifact[0].samples

        negative_controls: list = get_negative_controls_from_list(samples=samples)

        if len(negative_controls) > 1:
            sample_ids = [sample.id for sample in negative_controls]
            LOG.warning(f"Several internal negative control samples found: {' '.join(sample_ids)}")
        else:
            return negative_controls[0].id
    except Exception as exception_object:
        raise LimsDataError from exception_object


def get_internal_negative_control_id(lims: LimsAPI, case: Case) -> str:
    """Query lims to retrive internal_negative_control_id."""

    sample_internal_id = case.sample_ids[0]

    try:
        internal_negative_control_id: str = get_internal_negative_control_id_from_lims(
            lims=lims, sample_internal_id=sample_internal_id
        )
        return internal_negative_control_id
    except Exception as exception_object:
        raise CgError from exception_object


def get_internal_negative_control_sample_for_case(
    case: Case,
    status_db: Store,
    lims: LimsAPI,
) -> Sample:
    try:
        internal_negative_control_id: str = get_internal_negative_control_id(lims=lims, case=case)
        return status_db.get_sample_by_internal_id(internal_id=internal_negative_control_id)
    except Exception as exception_object:
        raise CgError() from exception_object


def get_mutant_pool_samples(case: Case, status_db: Store, lims: LimsAPI) -> MutantPoolSamples:
    samples: list[Sample] = case.samples
    for sample in samples:
        if sample.is_negative_control:
            external_negative_control = samples.pop(sample)
        break

    try:
        internal_negative_control = get_internal_negative_control_sample_for_case(
            case=case, status_db=status_db, lims=lims
        )
    except Exception as exception_object:
        raise CgError from exception_object

    return MutantPoolSamples(
        samples=samples,
        external_negative_control=external_negative_control,
        internal_negative_control=internal_negative_control,
    )


def get_quality_metrics(
    case_results_file_path: Path, case: Case, status_db: Store, lims: LimsAPI
) -> QualityMetrics:
    try:
        samples_results: dict[str, SampleResults] = MetricsParser.parse_samples_results(
            case=case, file_path=case_results_file_path
        )
    except Exception as exception_object:
        raise CgError(f"Not possible to retrieve results for case {case}.") from exception_object

    try:
        samples: MutantPoolSamples = get_mutant_pool_samples(
            case=case, status_db=status_db, lims=lims
        )
    except Exception as exception_object:
        raise CgError(f"Not possible to retrieve samples for case {case}.") from exception_object

    return QualityMetrics(results=samples_results, pool=samples)


def get_report_path(case_path: Path) -> Path:
    return case_path.joinpath(QUALITY_REPORT_FILE_NAME)

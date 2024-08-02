from cg.apps.lims.api import LimsAPI
from cg.constants.constants import MutantQC
from cg.constants.lims import LimsArtifactTypes, LimsProcess
from cg.exc import CgError, LimsDataError
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


def get_internal_negative_control_id(lims: LimsAPI, case: Case) -> str:
    """Query lims to retrive internal_negative_control_id for a mutant case sequenced in one pool."""

    sample_internal_id = case.sample_ids[0]
    internal_negative_control_id: str = lims.get_internal_negative_control_id_from_sample_in_pool(
        sample_internal_id=sample_internal_id, pooling_step=LimsProcess.COVID_POOLING_STEP
    )
    return internal_negative_control_id


def get_internal_negative_control_sample_for_case(
    case: Case,
    status_db: Store,
    lims: LimsAPI,
) -> Sample:
    internal_negative_control_id: str = get_internal_negative_control_id(lims=lims, case=case)
    return status_db.get_sample_by_internal_id(internal_id=internal_negative_control_id)


def get_mutant_pool_samples(case: Case, status_db: Store, lims: LimsAPI) -> MutantPoolSamples:
    samples = []
    external_negative_control = None

    for sample in case.samples:
        if sample.is_negative_control:
            external_negative_control = sample
            continue
        samples.append(sample)

    if not external_negative_control:
        raise CgError(f"No external negative control sample found for case {case}.")

    internal_negative_control: Sample = get_internal_negative_control_sample_for_case(
        case=case, status_db=status_db, lims=lims
    )

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
            case=case, results_file_path=case_results_file_path
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

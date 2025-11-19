import pytest

from cg.constants.constants import MicrosaltAppTags
from cg.meta.workflow.microsalt.metrics_parser.models import (
    MicrosaltSamtoolsStats,
    PicardMarkduplicate,
    SampleMetrics,
)
from cg.meta.workflow.microsalt.quality_controller.models import (
    CaseQualityResult,
    SampleQualityResult,
)
from cg.meta.workflow.microsalt.quality_controller.quality_controller import (
    MicroSALTQualityController,
)
from cg.store.store import Store


def create_sample_metrics(
    total_reads: int | None = 100,
    mapped_rate: float | None = 0.8,
    duplication_rate: float | None = 0.1,
    insert_size: int | None = 200,
    average_coverage: float | None = 30.0,
    coverage_10x: float | None = 95.0,
) -> SampleMetrics:
    return SampleMetrics(
        microsalt_samtools_stats=MicrosaltSamtoolsStats(
            total_reads=total_reads,
            mapped_rate=mapped_rate,
            average_coverage=average_coverage,
            coverage_10x=coverage_10x,
        ),
        picard_markduplicate=PicardMarkduplicate(
            insert_size=insert_size, duplication_rate=duplication_rate
        ),
    )


def create_quality_result(
    sample_id: str = "sample_1",
    passes_qc: bool = True,
    is_control: bool = False,
    application_tag: str = MicrosaltAppTags.MWRNXTR003,
    passes_reads_qc: bool = True,
    passes_mapping_qc: bool = True,
    passes_duplication_qc: bool = True,
    passes_inserts_qc: bool = True,
    passes_coverage_qc: bool = True,
    passes_10x_coverage_qc: bool = True,
) -> SampleQualityResult:
    return SampleQualityResult(
        sample_id=sample_id,
        passes_qc=passes_qc,
        is_control=is_control,
        application_tag=application_tag,
        passes_reads_qc=passes_reads_qc,
        passes_mapping_qc=passes_mapping_qc,
        passes_duplication_qc=passes_duplication_qc,
        passes_inserts_qc=passes_inserts_qc,
        passes_coverage_qc=passes_coverage_qc,
        passes_10x_coverage_qc=passes_10x_coverage_qc,
    )


@pytest.fixture
def quality_results() -> list[SampleQualityResult]:
    return [
        SampleQualityResult(
            sample_id="sample_1",
            passes_qc=False,
            is_control=True,
            application_tag=MicrosaltAppTags.MWRNXTR003,
            passes_reads_qc=True,
            passes_mapping_qc=True,
            passes_duplication_qc=False,
            passes_inserts_qc=True,
            passes_coverage_qc=True,
            passes_10x_coverage_qc=True,
        ),
        SampleQualityResult(
            sample_id="sample_2",
            passes_qc=True,
            is_control=False,
            application_tag=MicrosaltAppTags.MWRNXTR003,
            passes_reads_qc=True,
            passes_mapping_qc=True,
            passes_duplication_qc=True,
            passes_inserts_qc=True,
            passes_coverage_qc=True,
            passes_10x_coverage_qc=True,
        ),
        SampleQualityResult(
            sample_id="sample_3",
            passes_qc=False,
            is_control=False,
            application_tag=MicrosaltAppTags.MWRNXTR003,
            passes_reads_qc=False,
            passes_mapping_qc=True,
            passes_duplication_qc=False,
            passes_inserts_qc=True,
            passes_coverage_qc=True,
            passes_10x_coverage_qc=False,
        ),
    ]


@pytest.fixture
def case_result():
    return CaseQualityResult(
        passes_qc=False,
        control_passes_qc=True,
        urgent_passes_qc=True,
        non_urgent_passes_qc=True,
    )


@pytest.fixture
def quality_controller(store: Store) -> MicroSALTQualityController:
    return MicroSALTQualityController(store)

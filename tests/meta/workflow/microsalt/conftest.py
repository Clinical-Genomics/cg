import pytest
from cg.constants.constants import MicrosaltAppTags
from cg.meta.workflow.microsalt.metrics_parser.models import (
    MicrosaltSamtoolsStats,
    PicardMarkduplicate,
    SampleMetrics,
)

from cg.meta.workflow.microsalt.quality_controller.models import QualityResult


def create_sample_metrics(
    total_reads: int = 100,
    mapped_rate: float = 0.8,
    duplication_rate: float = 0.1,
    insert_size: int = 200,
    average_coverage: float = 30.0,
    coverage_10x: float = 95.0,
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


@pytest.fixture
def quality_results() -> list[QualityResult]:
    return [
        QualityResult(
            sample_id="sample1",
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
        QualityResult(
            sample_id="sample2",
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
        QualityResult(
            sample_id="sample3",
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

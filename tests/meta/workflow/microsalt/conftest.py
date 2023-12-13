import pytest
from cg.constants.constants import MicrosaltAppTags

from cg.meta.workflow.microsalt.quality_controller.models import QualityResult


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

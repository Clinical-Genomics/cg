from pathlib import Path

from cg.constants.constants import MicrosaltQC
from cg.io.json import read_json
from cg.meta.workflow.microsalt.models import QualityMetrics


def is_valid_total_reads(sample_reads: int, target_reads: int) -> bool:
    return sample_reads > target_reads * MicrosaltQC.TARGET_READS_FAIL_THRESHOLD


def is_valid_total_reads_for_control(sample_reads: int, target_reads: int) -> bool:
    return sample_reads < target_reads * MicrosaltQC.NEGATIVE_CONTROL_READS_THRESHOLD


def is_valid_mapped_rate(sample_mapped_rate: float) -> bool:
    return sample_mapped_rate > MicrosaltQC.MAPPED_RATE_THRESHOLD


def parse_quality_metrics(file_path: Path) -> QualityMetrics:
    data = read_json(file_path)
    return QualityMetrics.model_validate_json(data)

from cg.constants.constants import MicrosaltQC


def is_total_reads_above_failure_threshold(sample_reads: int, target_reads: int) -> bool:
    return sample_reads > target_reads * MicrosaltQC.TARGET_READS_FAIL_THRESHOLD

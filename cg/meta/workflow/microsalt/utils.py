from cg.constants.constants import MicrosaltQC


def is_valid_total_reads(sample_reads: int, target_reads: int) -> bool:
    return sample_reads > target_reads * MicrosaltQC.TARGET_READS_FAIL_THRESHOLD


def is_valid_total_reads_for_control(sample_reads: int, target_reads: int) -> bool:
    return sample_reads < target_reads * MicrosaltQC.NEGATIVE_CONTROL_READS_THRESHOLD

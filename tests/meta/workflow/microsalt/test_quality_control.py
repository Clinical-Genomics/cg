from cg.meta.workflow.microsalt.quality_controller.utils import is_valid_total_reads


def test_sample_total_reads_passing():
    # GIVEN a sample with sufficient reads
    sample_reads = 100
    target_reads = 100

    # WHEN checking if the sample has sufficient reads
    passes_reads_threshold = is_valid_total_reads(reads=sample_reads, target_reads=target_reads)

    # THEN it passes
    assert passes_reads_threshold


def test_sample_total_reads_failing():
    # GIVEN a sample with insufficient reads
    sample_reads = 50
    target_reads = 100

    # WHEN checking if the sample has sufficient reads
    passes_reads_threshold = is_valid_total_reads(reads=sample_reads, target_reads=target_reads)

    # THEN it fails
    assert not passes_reads_threshold


def test_sample_total_reads_failing_without_reads():
    # GIVEN a sample without reads
    sample_reads = 0
    target_reads = 100

    # WHEN checking if the sample has sufficient reads
    passes_reads_threshold = is_valid_total_reads(reads=sample_reads, target_reads=target_reads)

    # THEN it fails
    assert not passes_reads_threshold

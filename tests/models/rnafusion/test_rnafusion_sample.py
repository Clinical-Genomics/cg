from typing import List

from pydantic.v1 import ValidationError as PydanticValidationError
import pytest

from cg.models.rnafusion.rnafusion_sample import RnafusionSample


def test_instantiate_rnafusion_sample(
    rnafusion_sample: str,
    rnafusion_fastq_r1: List[str],
    rnafusion_fastq_r2_same_length: List[str],
    rnafusion_strandedness_acceptable: str,
):
    """
    Tests rnafusion sample.
    """
    # GIVEN a sample with fastq files and strandedness

    # WHEN instantiating a MipAnalysis object
    rnafusion_sample_object = RnafusionSample(
        sample=rnafusion_sample,
        fastq_r1=rnafusion_fastq_r1,
        fastq_r2=rnafusion_fastq_r2_same_length,
        strandedness=rnafusion_strandedness_acceptable,
    )

    # THEN assert that it was successfully created
    assert isinstance(rnafusion_sample_object, RnafusionSample)


def test_instantiate_rnafusion_sample_fastq_r1_r2_different_length(
    rnafusion_sample: str,
    rnafusion_fastq_r1: List[str],
    rnafusion_fastq_r2_not_same_length: List[str],
    rnafusion_strandedness_acceptable: str,
):
    """
    Tests rnafusion sample with different fastq_r1 and fastq_r2 length.
    """

    # GIVEN a sample with fastq files and strandedness

    # WHEN instantiating a sample object THEN throws a ValidationError

    with pytest.raises(PydanticValidationError):
        RnafusionSample(
            sample=rnafusion_sample,
            fastq_r1=rnafusion_fastq_r1,
            fastq_r2=rnafusion_fastq_r2_not_same_length,
            strandedness=rnafusion_strandedness_acceptable,
        )


def test_instantiate_rnafusion_sample_fastq_r2_empty(
    rnafusion_sample: str,
    rnafusion_fastq_r1: List[str],
    rnafusion_fastq_r2_empty: list,
    rnafusion_strandedness_acceptable: str,
):
    """
    Tests rnafusion sample with fastq_r2 empty (single end).
    """

    # GIVEN a sample with fastq files and strandedness

    # WHEN instantiating a sample object
    rnafusion_sample_object: RnafusionSample = RnafusionSample(
        sample=rnafusion_sample,
        fastq_r1=rnafusion_fastq_r1,
        fastq_r2=rnafusion_fastq_r2_empty,
        strandedness=rnafusion_strandedness_acceptable,
    )

    # THEN assert that it was successfully created
    assert isinstance(rnafusion_sample_object, RnafusionSample)


def test_instantiate_rnafusion_strandedness_not_acceptable(
    rnafusion_sample: str,
    rnafusion_fastq_r1: List[str],
    rnafusion_fastq_r2_same_length: List[str],
    rnafusion_strandedness_not_acceptable: str,
):
    """
    Tests rnafusion sample with unacceptable strandedness.
    """
    # WHEN instantiating a sample object THEN throws a ValidationError

    with pytest.raises(PydanticValidationError):
        RnafusionSample(
            sample=rnafusion_sample,
            fastq_r1=rnafusion_fastq_r1,
            fastq_r2=rnafusion_fastq_r2_same_length,
            strandedness=rnafusion_strandedness_not_acceptable,
        )

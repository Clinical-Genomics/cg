from typing import List

import pytest
from pydantic.v1 import ValidationError
from pydantic.v1 import ValidationError as PydanticValidationError

from cg.exc import SampleSheetError
from cg.models.rnafusion.rnafusion import RnafusionSample


def test_instantiate_rnafusion_sample(
    rnafusion_sample: str,
    rnafusion_fastq_forward: List[str],
    rnafusion_fastq_reverse_same_length: List[str],
    rnafusion_strandedness_acceptable: str,
):
    """
    Tests rnafusion sample.
    """
    # GIVEN a sample with fastq files and strandedness

    # WHEN instantiating a rnafusion sample object
    rnafusion_sample_object = RnafusionSample(
        sample=rnafusion_sample,
        fastq_forward=rnafusion_fastq_forward,
        fastq_reverse=rnafusion_fastq_reverse_same_length,
        strandedness=rnafusion_strandedness_acceptable,
    )

    # THEN assert that it was successfully created
    assert isinstance(rnafusion_sample_object, RnafusionSample)


def test_fastq_forward_reverse_different_length(
    rnafusion_sample: str,
    rnafusion_fastq_forward: List[str],
    rnafusion_fastq_reverse_not_same_length: List[str],
    rnafusion_strandedness_acceptable: str,
):
    """
    Tests rnafusion sample with different fastq_forward and fastq_reverse length.
    """
    # GIVEN a sample with fastq files of different lengths

    # WHEN instantiating a sample object

    # THEN throws an error
    with pytest.raises(SampleSheetError):
        RnafusionSample(
            sample=rnafusion_sample,
            fastq_forward=rnafusion_fastq_forward,
            fastq_reverse=rnafusion_fastq_reverse_not_same_length,
            strandedness=rnafusion_strandedness_acceptable,
        )


def test_fastq_empty_list(
    rnafusion_sample: str,
    rnafusion_fastq_forward: List[str],
    rnafusion_fastq_reverse_empty: list,
    rnafusion_strandedness_acceptable: str,
):
    """
    Tests rnafusion sample with a fastq_reverse empty list (single end).
    """

    # GIVEN a sample with fastq files and strandedness

    # WHEN instantiating a sample object
    with pytest.raises(ValidationError):
        RnafusionSample(
            sample=rnafusion_sample,
            fastq_forward=rnafusion_fastq_forward,
            fastq_reverse=rnafusion_fastq_reverse_empty,
            strandedness=rnafusion_strandedness_acceptable,
        )


def test_instantiate_rnafusion_strandedness_not_acceptable(
    rnafusion_sample: str,
    rnafusion_fastq_forward: List[str],
    rnafusion_fastq_reverse_same_length: List[str],
    rnafusion_strandedness_not_acceptable: str,
):
    """
    Tests rnafusion sample with unacceptable strandedness.
    """

    # WHEN instantiating a sample object THEN throws a ValidationError

    with pytest.raises(PydanticValidationError):
        RnafusionSample(
            sample=rnafusion_sample,
            fastq_forward=rnafusion_fastq_forward,
            fastq_reverse=rnafusion_fastq_reverse_same_length,
            strandedness=rnafusion_strandedness_not_acceptable,
        )

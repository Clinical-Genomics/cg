from pathlib import Path

import pytest
from pydantic.v1 import ValidationError

from cg.exc import NfSampleSheetError
from cg.models.rnafusion.rnafusion import RnafusionSampleSheetEntry


def test_instantiate_rnafusion_sample(
    sample_name: str,
    fastq_forward_read_path: Path,
    fastq_reverse_read_path: Path,
    strandedness: str,
):
    """
    Tests Rnafusion sample with correct values.
    """
    # GIVEN a sample with fastq files and strandedness

    # WHEN instantiating a rnafusion sample object
    rnafusion_sample_object = RnafusionSampleSheetEntry(
        name=sample_name,
        fastq_forward_read_paths=[fastq_forward_read_path, fastq_forward_read_path],
        fastq_reverse_read_paths=[fastq_reverse_read_path, fastq_reverse_read_path],
        strandedness=strandedness,
    )

    # THEN assert that it was successfully created
    assert isinstance(rnafusion_sample_object, RnafusionSampleSheetEntry)


def test_incomplete_fastq_file_pairs(
    sample_name: str,
    fastq_forward_read_path: Path,
    fastq_reverse_read_path: Path,
    strandedness: str,
):
    """
    Tests Rnafusion sample with lists of different length for fastq forward and reverse reads.
    """
    # GIVEN a sample with fastq files of different lengths

    # WHEN instantiating a sample object

    # THEN throws an error
    with pytest.raises(NfSampleSheetError) as error:
        RnafusionSampleSheetEntry(
            name=sample_name,
            fastq_forward_read_paths=[fastq_forward_read_path, fastq_forward_read_path],
            fastq_reverse_read_paths=[fastq_reverse_read_path],
            strandedness=strandedness,
        )
    assert "Fastq file length for forward and reverse do not match" in str(error.value)


def test_fastq_empty_list(
    sample_name: str,
    fastq_forward_read_path: Path,
    fastq_reverse_read_path: Path,
    strandedness: str,
):
    """
    Tests Rnafusion sample with a empty list for fastq reverse reads (single end).
    """

    # GIVEN a sample with fastq files and strandedness

    # WHEN instantiating a sample object

    # THEN throws an error
    with pytest.raises(ValidationError) as error:
        RnafusionSampleSheetEntry(
            name=sample_name,
            fastq_forward_read_paths=[fastq_forward_read_path, fastq_forward_read_path],
            fastq_reverse_read_paths=[],
            strandedness=strandedness,
        )
    assert "ensure this value has at least 1 items" in str(error.value)


def test_strandedness_not_permitted(
    sample_name: str,
    fastq_forward_read_path: Path,
    fastq_reverse_read_path: Path,
    strandedness_not_permitted: str,
):
    """
    Tests Rnafusion sample with not permitted strandedness.
    """

    # WHEN instantiating a sample object THEN throws a ValidationError
    with pytest.raises(ValidationError) as error:
        RnafusionSampleSheetEntry(
            name=sample_name,
            fastq_forward_read_paths=[fastq_forward_read_path],
            fastq_reverse_read_paths=[fastq_reverse_read_path],
            strandedness=strandedness_not_permitted,
        )
    assert "value is not a valid enumeration member" in str(error.value)


def test_non_existing_fastq_file(
    sample_name: str,
    fastq_forward_read_path: Path,
    non_existing_file_path: Path,
    strandedness: str,
):
    """
    Tests Rnafusion sample with non existing files
    """
    # GIVEN a sample with a non existing file

    # WHEN instantiating a sample object THEN throws an error
    with pytest.raises(NfSampleSheetError) as error:
        RnafusionSampleSheetEntry(
            name=sample_name,
            fastq_forward_read_paths=[fastq_forward_read_path],
            fastq_reverse_read_paths=[non_existing_file_path],
            strandedness=strandedness,
        )
    assert "Fastq file does not exist" in str(error.value)

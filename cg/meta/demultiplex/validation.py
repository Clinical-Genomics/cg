import logging
import re


LOG = logging.getLogger(__name__)

def validate_sample_fastq_file_name(sample_fastq_file_name: str) -> None:
    """
    Validate each part of the sample fastq file name.

    Pre-condition: The sample fastq file name should be in the format
    <flow_cell_id>_<sample_id>_<sample_index>_S<set_number>_L<lane_number>_R<read_number>_<segement_number>.fastq.gz

    Raises:
        - ValueError if the sample fastq file name is not in the expected format.
    """
    LOG.debug(f"Validating fastq file name {sample_fastq_file_name}")

    pattern = r"^([^_]*)_([^_]*)_([^_]*)_S(\d+)_L(\d+)_R(\d+)_(\d+)\.fastq\.gz$"
    match = re.fullmatch(pattern, sample_fastq_file_name)

    if not match:
        raise ValueError(
            f"Invalid fastq file name {sample_fastq_file_name}. Expected format: <flow_cell_id>_<sample_id>_<sample_index>_S<set_number>_L<lane_number>_R<read_number>_<segement_number>.fastq.gz"
        )

    (
        flow_cell_id,
        sample_id,
        sample_index,
        set_number,
        lane_number,
        read_number,
        segment_number,
    ) = match.groups()

    validate_non_empty_string(flow_cell_id, "flow cell ID")
    validate_non_empty_string(sample_id, "sample ID")
    validate_numeric_string(sample_index, "sample index")
    validate_numeric_string(set_number, "set number")
    validate_numeric_string(lane_number, "lane number")
    validate_numeric_string(read_number, "read number")
    validate_numeric_string(segment_number, "segment number")


def validate_non_empty_string(input_string: str, string_name: str) -> None:
    if not input_string:
        raise ValueError(f"Invalid {string_name} {input_string} in sample fastq file name.")

def validate_numeric_string(input_string: str, string_name: str) -> None:
    if not input_string.isdigit():
        raise ValueError(
            f"Invalid {string_name} {input_string} in fastq file name. {string_name.capitalize()} should be a digit."
        )

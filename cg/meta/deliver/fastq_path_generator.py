from pathlib import Path
from cg.constants.constants import ReadDirection, FileExtensions


def generate_concatenated_fastq_delivery_path(
    fastq_directory: Path, sample_name: str, direction: int
) -> Path:
    return Path(
        fastq_directory, f"{sample_name}_{direction}{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    )


def generate_forward_concatenated_fastq_delivery_path(
    fastq_directory: Path, sample_name: str
) -> Path:
    return generate_concatenated_fastq_delivery_path(
        fastq_directory=fastq_directory,
        sample_name=sample_name,
        direction=ReadDirection.FORWARD,
    )


def generate_reverse_concatenated_fastq_delivery_path(
    fastq_directory: Path, sample_name: str
) -> Path:
    return generate_concatenated_fastq_delivery_path(
        fastq_directory=fastq_directory,
        sample_name=sample_name,
        direction=ReadDirection.REVERSE,
    )

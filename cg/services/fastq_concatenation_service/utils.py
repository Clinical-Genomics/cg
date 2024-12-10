from pathlib import Path
import re
import shutil
import uuid

from cg.services.fastq_concatenation_service.exceptions import ConcatenationError
from cg.constants.constants import ReadDirection, FileFormat
from cg.constants import FileExtensions


def concatenate_fastq_reads_for_direction(
    directory: Path, sample_id: str, direction: ReadDirection
) -> Path | None:
    fastqs: list[Path] = get_fastqs_by_direction(
        fastq_directory=directory, direction=direction, sample_id=sample_id
    )
    if not fastqs:
        return
    output_file: Path = get_new_unique_file(directory)
    concatenate(input_files=fastqs, output_file=output_file)
    validate_concatenation(input_files=fastqs, output_file=output_file)
    return output_file


def get_new_unique_file(directory: Path) -> Path:
    unique_id = uuid.uuid4()
    return Path(directory, f"{unique_id}{FileExtensions.FASTQ}{FileExtensions.GZIP}")


def get_fastqs_by_direction(fastq_directory: Path, direction: int, sample_id: str) -> list[Path]:
    """Get fastq files by direction and sample id in a given directory.
    args:
    fastq_directory: Path: The directory containing the fastq files.
    direction: int: The direction of the reads.
    sample_id: str: The identifier to identify the samples by it should be a unique identifier in the file name.
    """
    pattern = f".*{sample_id}.*_R{direction}_[0-9]+{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    fastqs: list[Path] = []
    for file in fastq_directory.iterdir():
        if re.match(pattern, file.name):
            fastqs.append(file)
    return sort_files_by_name(fastqs)


def get_total_size(files: list[Path]) -> int:
    return sum(file.stat().st_size for file in files)


def concatenate(input_files: list[Path], output_file: Path) -> None:
    with open(output_file, "wb") as write_file_obj:
        for file in input_files:
            with open(file, "rb") as file_descriptor:
                shutil.copyfileobj(file_descriptor, write_file_obj)


def validate_concatenation(input_files: list[Path], output_file: Path) -> None:
    total_size: int = get_total_size(input_files)
    concatenated_size: int = get_total_size([output_file])
    if total_size != concatenated_size:
        raise ConcatenationError


def sort_files_by_name(files: list[Path]) -> list[Path]:
    return sorted(files, key=lambda file: file.name)


def file_can_be_removed(file: Path, forward_file: Path, reverse_file: Path, sample_id: str) -> bool:
    """
    Check if a file can be removed.
    args:
        file: Path: The file to check.
        forward_file: Path: The forward file.
        reverse_file: Path: The reverse file.
        sample_id: str: The identifier to identify the samples by it should be a unique identifier in the file name.
    """
    return (
        f"{FileFormat.FASTQ}{FileExtensions.GZIP}" in file.name
        and sample_id in file.name
        and file != forward_file
        and file != reverse_file
    )


def remove_raw_fastqs(
    fastq_directory: Path, forward_file: Path, reverse_file: Path, sample_id: str
) -> None:
    for file in fastq_directory.iterdir():
        if file_can_be_removed(
            file=file, forward_file=forward_file, reverse_file=reverse_file, sample_id=sample_id
        ):
            file.unlink()


def generate_concatenated_fastq_delivery_path(
    fastq_directory: Path, sample_name: str, direction: int
) -> Path:
    return Path(
        fastq_directory, f"{sample_name}_{direction}{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    )

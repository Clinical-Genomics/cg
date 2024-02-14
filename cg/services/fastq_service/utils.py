from pathlib import Path
import shutil

from cg.services.fastq_service.exceptions import InvalidConcatenationError


def remove_files(files: list[Path]) -> None:
    for file in files:
        file.unlink()


def get_total_size(files: list[Path]) -> int:
    return sum(file.stat().st_size for file in files)


def sort_files_by_name(files: list[Path]) -> list[Path]:
    files_map = {file_path.name: file_path for file_path in files}
    sorted_names = sorted(files_map.keys())
    return [files_map[name] for name in sorted_names]


def concatenate(input_files: list[Path], output_file: Path) -> None:
    with open(output_file, "wb") as write_file_obj:
        for file in input_files:
            with open(file, "rb") as file_descriptor:
                shutil.copyfileobj(file_descriptor, write_file_obj)


def validate_concatenation(input_files: list[Path], output_file: Path) -> None:
    total_size: int = get_total_size(input_files)
    concatenated_size: int = get_total_size([output_file])
    if total_size != concatenated_size:
        raise InvalidConcatenationError

from pathlib import Path

import pytest

from cg.services.deliver_files.file_fetcher.models import DeliveryFiles, SampleFile
from cg.services.deliver_files.file_formatter.models import FormattedFile


@pytest.fixture
def expected_formatted_analysis_case_files(
    expected_moved_analysis_delivery_files: DeliveryFiles,
) -> list[FormattedFile]:
    formatted_files: list[FormattedFile] = []
    for case_file in expected_moved_analysis_delivery_files.case_files:
        replaced_case_file_name: str = case_file.file_path.name.replace(
            case_file.case_id, case_file.case_name
        )
        formatted_file_path = Path(
            case_file.file_path.parent, case_file.case_name, replaced_case_file_name
        )
        formatted_files.append(
            FormattedFile(original_path=case_file.file_path, formatted_path=formatted_file_path)
        )
    return formatted_files


@pytest.fixture
def expected_formatted_analysis_sample_files(
    expected_moved_analysis_delivery_files: DeliveryFiles,
) -> list[FormattedFile]:
    formatted_files: list[FormattedFile] = []
    for sample_file in expected_moved_analysis_delivery_files.sample_files:
        replaced_sample_file_name: str = sample_file.file_path.name.replace(
            sample_file.sample_id, sample_file.sample_name
        )
        formatted_file_path = Path(
            sample_file.file_path.parent, sample_file.sample_name, replaced_sample_file_name
        )
        formatted_files.append(
            FormattedFile(original_path=sample_file.file_path, formatted_path=formatted_file_path)
        )
    return formatted_files


@pytest.fixture
def expected_formatted_fastq_sample_files(
    expected_moved_fastq_delivery_files: DeliveryFiles,
) -> list[FormattedFile]:
    formatted_files: list[FormattedFile] = []
    for sample_file in expected_moved_fastq_delivery_files.sample_files:
        replaced_sample_file_name: str = sample_file.file_path.name.replace(
            sample_file.sample_id, sample_file.sample_name
        )
        formatted_file_path = Path(
            sample_file.file_path.parent, sample_file.sample_name, replaced_sample_file_name
        )
        formatted_files.append(
            FormattedFile(original_path=sample_file.file_path, formatted_path=formatted_file_path)
        )
    return formatted_files


@pytest.fixture
def expected_concatenated_fastq_formatted_files(
    fastq_concatenation_sample_files,
) -> list[FormattedFile]:
    formatted_files: list[FormattedFile] = []
    for sample_file in fastq_concatenation_sample_files:
        replaced_sample_file_name: str = sample_file.file_path.name.replace(
            sample_file.sample_id, sample_file.sample_name
        )
        replaced_sample_file_name = replaced_sample_file_name.replace("1_R1_1", "1")
        replaced_sample_file_name = replaced_sample_file_name.replace("2_R1_1", "1")
        replaced_sample_file_name = replaced_sample_file_name.replace("1_R2_1", "2")
        replaced_sample_file_name = replaced_sample_file_name.replace("2_R2_1", "2")
        formatted_file_path = Path(
            sample_file.file_path.parent, sample_file.sample_name, replaced_sample_file_name
        )
        formatted_files.append(
            FormattedFile(original_path=sample_file.file_path, formatted_path=formatted_file_path)
        )
    return formatted_files


@pytest.fixture
def empty_case_files() -> list:
    return []

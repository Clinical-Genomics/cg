from pathlib import Path
from unittest.mock import Mock

import pytest

from cg.services.deliver_files.file_fetcher.models import DeliveryFiles
from cg.services.deliver_files.file_formatter.destination.models import FormattedFile
from cg.services.deliver_files.file_formatter.files.concatenation_service import (
    SampleFileConcatenationFormatter,
)


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
def expected_flat_formatted_analysis_sample_files(
    expected_moved_analysis_delivery_files: DeliveryFiles,
) -> list[FormattedFile]:
    formatted_files: list[FormattedFile] = []
    for sample_file in expected_moved_analysis_delivery_files.sample_files:
        replaced_sample_file_name: str = sample_file.file_path.name.replace(
            sample_file.sample_id, sample_file.sample_name
        )
        formatted_file_path = Path(sample_file.file_path.parent, replaced_sample_file_name)
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
        replaced_sample_file_name = replaced_sample_file_name.replace("L001_R1_001", "1")
        replaced_sample_file_name = replaced_sample_file_name.replace("L002_R1_001", "1")
        replaced_sample_file_name = replaced_sample_file_name.replace("L001_R2_001", "2")
        replaced_sample_file_name = replaced_sample_file_name.replace("L002_R2_001", "2")
        replaced_sample_file_name = replaced_sample_file_name.replace("FC_", "")
        formatted_file_path = Path(
            sample_file.file_path.parent, sample_file.sample_name, replaced_sample_file_name
        )
        formatted_files.append(
            FormattedFile(original_path=sample_file.file_path, formatted_path=formatted_file_path)
        )
    return formatted_files


@pytest.fixture
def expected_concatenated_fastq_flat_formatted_files(
    fastq_concatenation_sample_files_flat,
) -> list[FormattedFile]:
    formatted_files: list[FormattedFile] = []
    for sample_file in fastq_concatenation_sample_files_flat:
        replaced_sample_file_name: str = sample_file.file_path.name.replace(
            sample_file.sample_id, sample_file.sample_name
        )
        replaced_sample_file_name = replaced_sample_file_name.replace("L001_R1_001", "1")
        replaced_sample_file_name = replaced_sample_file_name.replace("L002_R1_001", "1")
        replaced_sample_file_name = replaced_sample_file_name.replace("L001_R2_001", "2")
        replaced_sample_file_name = replaced_sample_file_name.replace("L002_R2_001", "2")
        replaced_sample_file_name = replaced_sample_file_name.replace("FC_", "")
        formatted_file_path = Path(sample_file.file_path.parent, replaced_sample_file_name)
        formatted_files.append(
            FormattedFile(original_path=sample_file.file_path, formatted_path=formatted_file_path)
        )
    return formatted_files


@pytest.fixture
def empty_case_files() -> list:
    return []

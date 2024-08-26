from pathlib import Path

import pytest

from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles, SampleFile
from cg.services.file_delivery.file_formatter_service.models import FormattedFile


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
def fastq_sample_files(tmp_path: Path) -> list[SampleFile]:
    some_ticket: str = "some_ticket"
    fastq_paths: list[Path] = [
        Path(tmp_path, some_ticket, "S1_1_R1.fastq.gz"),
        Path(tmp_path, some_ticket, "S1_2_R1.fastq.gz"),
        Path(tmp_path, some_ticket, "S1_1_R2.fastq.gz"),
        Path(tmp_path, some_ticket, "S1_2_R2.fastq.gz"),
    ]
    return [
        SampleFile(
            sample_id="S1",
            case_id="Case1",
            sample_name="Sample1",
            file_path=fastq_path,
        )
        for fastq_path in fastq_paths
    ]


@pytest.fixture
def expected_concatenated_fastq_formatted_files(
    fastq_sample_files: list[SampleFile],
) -> list[FormattedFile]:
    formatted_files: list[FormattedFile] = []
    for sample_file in fastq_sample_files:
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

import os
from pathlib import Path

from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.file_delivery.fetch_file_service.models import SampleFile
from cg.services.file_delivery.file_formatter_service.models import FormattedFile
from cg.services.file_delivery.file_formatter_service.utils.sample_file_concatenation_formatter import (
    SampleFileConcatenationFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_formatter import (
    SampleFileFormatter,
)


def test_sample_file_concatenation_formatter(
    fastq_sample_files: list[SampleFile],
    expected_concatenated_fastq_formatted_files: list[FormattedFile],
):
    # GIVEN existing case files, a case file formatter and a ticket directory path and a customer inbox
    sample_file_formatter = SampleFileConcatenationFormatter(
        concatenation_service=FastqConcatenationService()
    )
    ticket_dir_path: Path = fastq_sample_files[0].file_path.parent
    os.makedirs(ticket_dir_path, exist_ok=True)
    for sample_file in fastq_sample_files:
        sample_file.file_path.touch()

    # WHEN formatting the case files
    formatted_files: list[FormattedFile] = sample_file_formatter.format_files(
        sample_files=fastq_sample_files,
        ticket_dir_path=ticket_dir_path,
    )

    # THEN the case files should be formatted
    assert formatted_files == expected_concatenated_fastq_formatted_files
    for file in formatted_files:
        assert file.formatted_path.exists()
        assert not file.original_path.exists()

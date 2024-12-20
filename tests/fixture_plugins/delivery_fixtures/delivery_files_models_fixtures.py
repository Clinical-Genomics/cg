import os
from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.delivery import INBOX_NAME
from cg.constants.housekeeper_tags import (
    HK_DELIVERY_REPORT_TAG,
    AlignmentFileTag,
    SequencingFileTag,
)
from cg.services.deliver_files.file_fetcher.models import (
    CaseFile,
    DeliveryFiles,
    DeliveryMetaData,
    SampleFile,
)
from cg.services.deliver_files.file_formatter.destination.models import FormattedFile
from cg.store.models import Case
from cg.store.store import Store


@pytest.fixture
def expected_fastq_delivery_files(
    delivery_housekeeper_api: HousekeeperAPI,
    case_id: str,
    sample_id: str,
    sample_name: str,
    another_sample_id: str,
    another_sample_name: str,
    delivery_store_microsalt: Store,
) -> DeliveryFiles:
    """Return the expected fastq delivery files."""
    sample_info: list[tuple[str, str]] = [
        (sample_id, sample_name),
        (another_sample_id, another_sample_name),
    ]
    sample_files: list[SampleFile] = [
        SampleFile(
            case_id=case_id,
            sample_id=sample[0],
            sample_name=sample[1],
            file_path=delivery_housekeeper_api.get_files_from_latest_version(
                bundle_name=sample[0], tags=[SequencingFileTag.FASTQ]
            )[0].full_path,
        )
        for sample in sample_info
    ]
    case: Case = delivery_store_microsalt.get_case_by_internal_id(case_id)
    delivery_meta_data = DeliveryMetaData(
        case_id=case.internal_id,
        customer_internal_id=case.customer.internal_id,
        ticket_id=case.latest_ticket,
    )
    return DeliveryFiles(delivery_data=delivery_meta_data, case_files=[], sample_files=sample_files)


@pytest.fixture
def expected_bam_delivery_files(
    delivery_housekeeper_api: HousekeeperAPI,
    case_id: str,
    sample_id: str,
    sample_name: str,
    another_sample_id: str,
    another_sample_name: str,
    delivery_store_microsalt: Store,
) -> DeliveryFiles:
    """Return the expected fastq delivery files."""
    sample_info: list[tuple[str, str]] = [
        (sample_id, sample_name),
        (another_sample_id, another_sample_name),
    ]
    sample_files: list[SampleFile] = [
        SampleFile(
            case_id=case_id,
            sample_id=sample[0],
            sample_name=sample[1],
            file_path=delivery_housekeeper_api.get_files_from_latest_version(
                bundle_name=sample[0], tags=[AlignmentFileTag.BAM]
            )[0].full_path,
        )
        for sample in sample_info
    ]
    case: Case = delivery_store_microsalt.get_case_by_internal_id(case_id)
    delivery_meta_data = DeliveryMetaData(
        case_id=case.internal_id,
        customer_internal_id=case.customer.internal_id,
        ticket_id=case.latest_ticket,
    )
    return DeliveryFiles(delivery_data=delivery_meta_data, case_files=[], sample_files=sample_files)


@pytest.fixture()
def expected_bam_delivery_files_single_sample(
    expected_bam_delivery_files: DeliveryFiles, sample_id: str
) -> DeliveryFiles:
    expected_bam_delivery_files.sample_files = [
        sample_file
        for sample_file in expected_bam_delivery_files.sample_files
        if sample_file.sample_id == sample_id
    ]
    return expected_bam_delivery_files


@pytest.fixture
def expected_fohm_delivery_files(
    delivery_fohm_upload_housekeeper_api: HousekeeperAPI,
    case_id: str,
    case_name: str,
    sample_id: str,
    sample_name: str,
    another_sample_id: str,
    another_sample_name: str,
    delivery_store_mutant: Store,
) -> DeliveryFiles:
    """Return the expected fastq delivery files."""
    sample_info: list[tuple[str, str]] = [
        (sample_id, sample_name),
        (another_sample_id, another_sample_name),
    ]
    sample_files: list[SampleFile] = [
        SampleFile(
            case_id=case_id,
            sample_id=sample[0],
            sample_name=sample[1],
            file_path=delivery_fohm_upload_housekeeper_api.get_files_from_latest_version(
                bundle_name=sample[0], tags=[SequencingFileTag.FASTQ]
            )[0].full_path,
        )
        for sample in sample_info
    ]
    case_sample_info: list[tuple[str, str, str]] = [
        (sample_id, sample_name, "consensus-sample"),
        (sample_id, sample_name, "vcf-report"),
        (another_sample_id, another_sample_name, "consensus-sample"),
        (another_sample_id, another_sample_name, "vcf-report"),
    ]
    case_sample_files: list[SampleFile] = [
        SampleFile(
            case_id=case_id,
            sample_id=sample[0],
            sample_name=sample[1],
            file_path=delivery_fohm_upload_housekeeper_api.get_files_from_latest_version_containing_tags(
                bundle_name=case_id, tags=[{sample[2], sample[0]}]
            )[
                0
            ].full_path,
        )
        for sample in case_sample_info
    ]

    case: Case = delivery_store_mutant.get_case_by_internal_id(case_id)
    delivery_meta_data = DeliveryMetaData(
        case_id=case.internal_id,
        customer_internal_id=case.customer.internal_id,
        ticket_id=case.latest_ticket,
    )
    return DeliveryFiles(
        delivery_data=delivery_meta_data,
        case_files=[],
        sample_files=case_sample_files + sample_files,
    )


@pytest.fixture
def expected_analysis_delivery_files(
    delivery_housekeeper_api: HousekeeperAPI,
    case_id: str,
    case_name: str,
    sample_id: str,
    sample_name: str,
    another_sample_id: str,
    another_sample_name: str,
    delivery_store_balsamic: Store,
) -> DeliveryFiles:
    """Return the expected analysis delivery files."""
    sample_info: list[tuple[str, str]] = [
        (sample_id, sample_name),
        (another_sample_id, another_sample_name),
    ]
    sample_files: list[SampleFile] = []
    for sample in sample_info:
        sample_files.extend(
            [
                SampleFile(
                    case_id=case_id,
                    sample_id=sample[0],
                    sample_name=sample[1],
                    file_path=file.full_path,
                )
                for file in delivery_housekeeper_api.get_files_from_latest_version(
                    bundle_name=case_id, tags=[AlignmentFileTag.CRAM, sample[0]]
                )
            ]
        )
    case_files: list[CaseFile] = [
        CaseFile(
            case_id=case_id,
            case_name=case_name,
            file_path=delivery_housekeeper_api.get_files_from_latest_version(
                bundle_name=case_id, tags=[HK_DELIVERY_REPORT_TAG]
            )[0].full_path,
        )
    ]
    case: Case = delivery_store_balsamic.get_case_by_internal_id(case_id)
    delivery_meta_data = DeliveryMetaData(
        case_id=case.internal_id,
        customer_internal_id=case.customer.internal_id,
        ticket_id=case.latest_ticket,
    )
    return DeliveryFiles(
        delivery_data=delivery_meta_data, case_files=case_files, sample_files=sample_files
    )


@pytest.fixture
def expected_moved_fastq_delivery_files(
    expected_fastq_delivery_files: DeliveryFiles, tmp_path: Path
) -> DeliveryFiles:
    """Return the moved FASTQ delivery files."""
    delivery_files = DeliveryFiles(**expected_fastq_delivery_files.model_dump())
    inbox_dir_path = Path(
        tmp_path,
        delivery_files.delivery_data.customer_internal_id,
        INBOX_NAME,
        delivery_files.delivery_data.ticket_id,
    )
    delivery_files.delivery_data.delivery_path = inbox_dir_path
    new_sample_files: list[SampleFile] = swap_file_paths_with_inbox_paths(
        file_models=delivery_files.sample_files, inbox_dir_path=inbox_dir_path
    )
    return DeliveryFiles(
        delivery_data=expected_fastq_delivery_files.delivery_data,
        case_files=[],
        sample_files=new_sample_files,
    )


@pytest.fixture
def expected_moved_analysis_delivery_files(
    expected_analysis_delivery_files: DeliveryFiles, tmp_path: Path
) -> DeliveryFiles:
    """Return the moved analysis delivery files."""
    delivery_files = DeliveryFiles(**expected_analysis_delivery_files.model_dump())
    inbox_dir_path = Path(
        tmp_path,
        delivery_files.delivery_data.customer_internal_id,
        INBOX_NAME,
        delivery_files.delivery_data.ticket_id,
    )
    delivery_files.delivery_data.delivery_path = inbox_dir_path
    new_case_files: list[CaseFile] = swap_file_paths_with_inbox_paths(
        file_models=delivery_files.case_files, inbox_dir_path=inbox_dir_path
    )
    new_sample_files: list[SampleFile] = swap_file_paths_with_inbox_paths(
        file_models=delivery_files.sample_files, inbox_dir_path=inbox_dir_path
    )

    return DeliveryFiles(
        delivery_data=delivery_files.delivery_data,
        case_files=new_case_files,
        sample_files=new_sample_files,
    )


@pytest.fixture
def empty_delivery_files() -> DeliveryFiles:
    """Return an empty delivery files object."""
    delivery_data = DeliveryMetaData(
        case_id="some_case", customer_internal_id="cust_id", ticket_id="ticket_id"
    )
    return DeliveryFiles(delivery_data=delivery_data, case_files=[], sample_files=[])


@pytest.fixture
def expected_moved_analysis_sample_delivery_files(
    expected_moved_analysis_delivery_files: DeliveryFiles,
) -> list[SampleFile]:
    return expected_moved_analysis_delivery_files.sample_files


@pytest.fixture
def expected_moved_analysis_case_delivery_files(
    expected_moved_analysis_delivery_files: DeliveryFiles,
) -> list[CaseFile]:
    return expected_moved_analysis_delivery_files.case_files


@pytest.fixture
def fastq_concatenation_sample_files(
    tmp_path: Path, expected_fastq_delivery_files: DeliveryFiles
) -> list[SampleFile]:
    """
    Return a list of sample files that are to be concatenated.
    """
    inbox = Path(
        expected_fastq_delivery_files.delivery_data.customer_internal_id,
        INBOX_NAME,
        expected_fastq_delivery_files.delivery_data.ticket_id,
    )
    sample_data = [("Sample_ID1", "Sample_Name1"), ("Sample_ID2", "Sample_Name2")]
    sample_files = []
    for sample_id, sample_name in sample_data:
        fastq_paths: list[Path] = [
            Path(tmp_path, inbox, f"FC_{sample_id}_L001_R1_001.fastq.gz"),
            Path(tmp_path, inbox, f"FC_{sample_id}_L002_R1_001.fastq.gz"),
            Path(tmp_path, inbox, f"FC_{sample_id}_L001_R2_001.fastq.gz"),
            Path(tmp_path, inbox, f"FC_{sample_id}_L002_R2_001.fastq.gz"),
        ]

        sample_files.extend(
            [
                SampleFile(
                    sample_id=sample_id,
                    case_id="Case1",
                    sample_name=sample_name,
                    file_path=fastq_path,
                )
                for fastq_path in fastq_paths
            ]
        )
    return sample_files


@pytest.fixture
def fastq_concatenation_sample_files_flat(tmp_path: Path) -> list[SampleFile]:
    sample_data = [("Sample_ID2", "Sample_Name2"), ("Sample_ID1", "Sample_Name1")]
    sample_files = []
    for sample_id, sample_name in sample_data:
        fastq_paths: list[Path] = [
            Path(tmp_path, f"FC_{sample_id}_L001_R1_001.fastq.gz"),
            Path(tmp_path, f"FC_{sample_id}_L002_R1_001.fastq.gz"),
            Path(tmp_path, f"FC_{sample_id}_L001_R2_001.fastq.gz"),
            Path(tmp_path, f"FC_{sample_id}_L002_R2_001.fastq.gz"),
        ]

        sample_files.extend(
            [
                SampleFile(
                    sample_id=sample_id,
                    case_id="Case1",
                    sample_name=sample_name,
                    file_path=fastq_path,
                )
                for fastq_path in fastq_paths
            ]
        )
    return sample_files


def swap_file_paths_with_inbox_paths(
    file_models: list[CaseFile | SampleFile], inbox_dir_path: Path
) -> list[CaseFile | SampleFile]:
    """Swap the file paths with the inbox paths."""
    new_file_models: list[SampleFile | CaseFile] = []
    for file_model in file_models:
        new_file_model: SampleFile = file_model
        new_file_model.file_path = Path(inbox_dir_path, file_model.file_path.name)
        new_file_models.append(new_file_model)
    return new_file_models


@pytest.fixture
def lims_naming_metadata() -> str:
    return "01_SE100_"


@pytest.fixture
def expected_mutant_formatted_files(
    expected_concatenated_fastq_formatted_files, lims_naming_metadata
) -> list[FormattedFile]:
    unique_combinations = []
    for formatted_file in expected_concatenated_fastq_formatted_files:
        formatted_file.original_path = formatted_file.formatted_path
        formatted_file.formatted_path = Path(
            formatted_file.formatted_path.parent,
            f"{lims_naming_metadata}{formatted_file.formatted_path.name}",
        )
        if formatted_file not in unique_combinations:
            unique_combinations.append(formatted_file)
    return unique_combinations


@pytest.fixture
def mutant_moved_files(fastq_concatenation_sample_files) -> list[SampleFile]:
    return fastq_concatenation_sample_files


@pytest.fixture
def expected_upload_files(expected_analysis_delivery_files: DeliveryFiles):
    return expected_analysis_delivery_files


@pytest.fixture
def expected_moved_upload_files(expected_analysis_delivery_files: DeliveryFiles, tmp_path: Path):
    delivery_files = DeliveryFiles(**expected_analysis_delivery_files.model_dump())
    delivery_files.delivery_data.delivery_path = tmp_path
    new_case_files: list[CaseFile] = swap_file_paths_with_inbox_paths(
        file_models=delivery_files.case_files, inbox_dir_path=tmp_path
    )
    new_sample_files: list[SampleFile] = swap_file_paths_with_inbox_paths(
        file_models=delivery_files.sample_files, inbox_dir_path=tmp_path
    )

    return DeliveryFiles(
        delivery_data=delivery_files.delivery_data,
        case_files=new_case_files,
        sample_files=new_sample_files,
    )


@pytest.fixture
def empty_sample() -> None:
    return None

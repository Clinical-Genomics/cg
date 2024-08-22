from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.delivery import INBOX_NAME
from cg.constants.housekeeper_tags import (
    HK_DELIVERY_REPORT_TAG,
    AlignmentFileTag,
    SequencingFileTag,
)
from cg.services.file_delivery.fetch_file_service.models import (
    DeliveryFiles,
    SampleFile,
    CaseFile,
    DeliveryMetaData,
)
from cg.store.models import Case
from cg.store.store import Store


@pytest.fixture
def expected_fastq_delivery_files(
    delivery_housekeeper_api: HousekeeperAPI,
    case_id: str,
    sample_id: str,
    another_sample_id: str,
    delivery_store_microsalt: Store,
) -> DeliveryFiles:
    """Return the expected fastq delivery files."""
    hk_bundle_names: list[str] = [sample_id, another_sample_id]
    sample_files: list[SampleFile] = [
        SampleFile(
            case_id=case_id,
            sample_id=sample,
            file_path=delivery_housekeeper_api.get_files_from_latest_version(
                bundle_name=sample, tags=[SequencingFileTag.FASTQ]
            )[0].full_path,
        )
        for sample in hk_bundle_names
    ]
    case: Case = delivery_store_microsalt.get_case_by_internal_id(case_id)
    delivery_data = DeliveryMetaData(
        customer_internal_id=case.customer.internal_id, ticket_id=case.latest_ticket
    )
    return DeliveryFiles(delivery_data=delivery_data, case_files=None, sample_files=sample_files)


@pytest.fixture
def expected_analysis_delivery_files(
    delivery_housekeeper_api: HousekeeperAPI,
    case_id: str,
    sample_id: str,
    another_sample_id: str,
    delivery_store_balsamic: Store,
) -> DeliveryFiles:
    """Return the expected analysis delivery files."""
    hk_bundle_names: list[str] = [sample_id, another_sample_id]
    sample_files: list[SampleFile] = []
    for sample in hk_bundle_names:
        sample_files.extend(
            [
                SampleFile(
                    case_id=case_id,
                    sample_id=sample,
                    file_path=file.full_path,
                )
                for file in delivery_housekeeper_api.get_files_from_latest_version(
                    bundle_name=case_id, tags=[AlignmentFileTag.CRAM, sample]
                )
            ]
        )
    case_files: list[CaseFile] = [
        CaseFile(
            case_id=case_id,
            file_path=delivery_housekeeper_api.get_files_from_latest_version(
                bundle_name=case_id, tags=[HK_DELIVERY_REPORT_TAG]
            )[0].full_path,
        )
    ]
    case: Case = delivery_store_balsamic.get_case_by_internal_id(case_id)
    delivery_data = DeliveryMetaData(
        customer_internal_id=case.customer.internal_id, ticket_id=case.latest_ticket
    )
    return DeliveryFiles(
        delivery_data=delivery_data, case_files=case_files, sample_files=sample_files
    )


@pytest.fixture
def expected_moved_fastq_delivery_files(
    expected_fastq_delivery_files: DeliveryFiles, tmp_path
) -> DeliveryFiles:
    """Return the moved FASTQ delivery files."""
    delivery_files = DeliveryFiles(**expected_fastq_delivery_files.model_dump())
    inbox_path: Path = Path(
        tmp_path,
        delivery_files.delivery_data.customer_internal_id,
        INBOX_NAME,
        delivery_files.delivery_data.ticket_id,
    )
    new_sample_files: list[SampleFile] = swap_file_paths_with_inbox_paths(
        delivery_files.sample_files, inbox_path
    )
    return DeliveryFiles(
        delivery_data=expected_fastq_delivery_files.delivery_data,
        case_files=None,
        sample_files=new_sample_files,
    )


@pytest.fixture
def expected_moved_analysis_delivery_files(
    expected_analysis_delivery_files: DeliveryFiles, tmp_path
) -> DeliveryFiles:
    """Return the moved analysis delivery files."""
    delivery_files = DeliveryFiles(**expected_analysis_delivery_files.model_dump())
    inbox_path: Path = Path(
        tmp_path,
        delivery_files.delivery_data.customer_internal_id,
        INBOX_NAME,
        delivery_files.delivery_data.ticket_id,
    )
    new_case_files: list[CaseFile] = swap_file_paths_with_inbox_paths(
        delivery_files.case_files, inbox_path
    )
    new_sample_files: list[SampleFile] = swap_file_paths_with_inbox_paths(
        delivery_files.sample_files, inbox_path
    )
    return DeliveryFiles(
        delivery_data=delivery_files.delivery_data,
        case_files=new_case_files,
        sample_files=new_sample_files,
    )


def swap_file_paths_with_inbox_paths(
    file_models: list[CaseFile | SampleFile], inbox_path: Path
) -> list[CaseFile | SampleFile]:
    """Swap the file paths with the inbox paths."""
    new_file_models: list[SampleFile | CaseFile] = []
    for file_model in file_models:
        new_file_model: SampleFile = file_model
        new_file_model.file_path = Path(inbox_path, file_model.file_path.name)
        new_file_models.append(new_file_model)
    return new_file_models

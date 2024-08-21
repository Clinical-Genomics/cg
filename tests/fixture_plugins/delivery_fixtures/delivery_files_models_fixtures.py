import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
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
def moved_fastq_delivery_files(expected_fastq_delivery_files: DeliveryFiles) -> DeliveryFiles:
    """Return the moved fastq delivery files."""
    return expected_fastq_delivery_files

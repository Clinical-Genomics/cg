import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.housekeeper_tags import (
    HK_DELIVERY_REPORT_TAG,
    AlignmentFileTag,
    SequencingFileTag,
)
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles, SampleFile, CaseFile


@pytest.fixture
def expected_fastq_delivery_files(
    delivery_housekeeper_api: HousekeeperAPI,
    case_id: str,
    sample_id: str,
    another_sample_id: str,
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
    return DeliveryFiles(case_files=None, sample_files=sample_files)


@pytest.fixture
def expected_analysis_delivery_files(
    delivery_housekeeper_api: HousekeeperAPI,
    case_id: str,
    sample_id: str,
    another_sample_id: str,
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
    return DeliveryFiles(case_files=case_files, sample_files=sample_files)

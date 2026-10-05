from pathlib import Path
from unittest.mock import Mock, create_autospec

from housekeeper.store.models import File, Tag
from pytest_mock import MockerFixture

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants.scout import RAREDISEASE_CASE_TAGS
from cg.meta.delivery.delivery import DeliveryAPI
from cg.meta.delivery_report.raredisease import RarediseaseDeliveryReportAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.delivery_report.report import ScoutVariantsFiles
from cg.store.store import Store


def test_get_scout_variants_files_all_files_present(mocker: MockerFixture):
    # GIVEN both a mitochondrial and a non-mitochondrial snv vcf file exists in Housekeeper
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)

    vcf_snv_tag = create_autospec(Tag)
    vcf_snv_tag.name = "vcf-snv-clinical"
    mitochondria_tag = create_autospec(Tag)
    mitochondria_tag.name = "mitochondria"
    clinical_snv_file = create_autospec(File, tags=[vcf_snv_tag], full_path="/path/to/snv.vcf")
    clinical_snv_mitochondrial_file = create_autospec(
        File, tags=[vcf_snv_tag, mitochondria_tag], full_path="/path/to/mitochondrial_snv.vcf"
    )
    housekeeper_api.get_files_from_latest_version = Mock(
        return_value=[clinical_snv_file, clinical_snv_mitochondrial_file]
    )

    def mock_get_latest_file(
        bundle: str, tags: list[str] | None = None, version: int | None = None
    ):
        vcf_str_file = create_autospec(File, full_path="/path/to/str.vcf")
        smn_tsv_file = create_autospec(File, full_path="/path/to/smn.tsv")
        if not tags:
            return None
        elif "vcf-str" in tags:
            return vcf_str_file
        elif "smn-calling" in tags:
            return smn_tsv_file
        else:
            return None

    housekeeper_api.get_latest_file = mock_get_latest_file

    # GIVEN a RarediseaseDeliveryReportAPI
    raredisease_analysis_api: RarediseaseAnalysisAPI = create_autospec(
        RarediseaseAnalysisAPI,
        delivery_api=create_autospec(DeliveryAPI),
        housekeeper_api=housekeeper_api,
        lims_api=create_autospec(LimsAPI),
        scout_api=create_autospec(ScoutAPI),
        status_db=create_autospec(Store),
    )
    raredisease_analysis_api.get_scout_upload_case_tags = Mock(return_value=RAREDISEASE_CASE_TAGS)
    delivery_report_api = RarediseaseDeliveryReportAPI(analysis_api=raredisease_analysis_api)

    # GIVEN that all files exist
    mocker.patch.object(Path, "is_file", return_value=True)

    # WHEN getting the scout variants files
    scout_variants_files: ScoutVariantsFiles = delivery_report_api.get_scout_variants_files(
        "case_id"
    )

    # THEN all the files should be there
    assert scout_variants_files.snv_vcf == "snv.vcf"
    assert scout_variants_files.snv_vcf_mt == "mitochondrial_snv.vcf"
    assert scout_variants_files.vcf_str == "str.vcf"
    assert scout_variants_files.smn_tsv == "smn.tsv"


def test_get_scout_variants_files_no_files_present(mocker: MockerFixture):
    # GIVEN no files exist in housekeeper
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)

    housekeeper_api.get_files_from_latest_version = Mock(return_value=[])
    housekeeper_api.get_latest_file = Mock(return_value=None)

    # GIVEN a RarediseaseDeliveryReportAPI
    raredisease_analysis_api = create_autospec(
        RarediseaseAnalysisAPI,
        delivery_api=create_autospec(DeliveryAPI),
        housekeeper_api=housekeeper_api,
        lims_api=create_autospec(LimsAPI),
        scout_api=create_autospec(ScoutAPI),
        status_db=create_autospec(Store),
    )
    raredisease_analysis_api.get_scout_upload_case_tags = Mock(return_value=RAREDISEASE_CASE_TAGS)
    delivery_report_api = RarediseaseDeliveryReportAPI(analysis_api=raredisease_analysis_api)

    # GIVEN that any file checked for exists
    mocker.patch.object(Path, "is_file", return_value=True)

    # WHEN getting the scout variants files
    scout_variants_files: ScoutVariantsFiles = delivery_report_api.get_scout_variants_files(
        "case_id"
    )

    # THEN all files should be set as "N/A"
    assert scout_variants_files.snv_vcf == "N/A"
    assert scout_variants_files.snv_vcf_mt == "N/A"
    assert scout_variants_files.vcf_str == "N/A"
    assert scout_variants_files.smn_tsv == "N/A"

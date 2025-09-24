"""Test Balsamic observations API."""

import logging
from pathlib import Path
from unittest.mock import ANY, Mock, create_autospec

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture, MockFixture
from sqlalchemy.orm import Session

from cg.apps.lims import LimsAPI
from cg.apps.loqus import LoqusdbAPI
from cg.constants.constants import CancerAnalysisType, CustomerId
from cg.constants.observations import LOQUSDB_ID, BalsamicObservationPanel, LoqusdbInstance
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import LoqusdbDuplicateRecordError
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.observations_api import ObservationsAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig, IlluminaConfig, RunInstruments
from cg.models.observations.input_files import BalsamicObservationsInputFiles
from cg.store.models import Bed, BedVersion, Case, Customer, Sample
from cg.store.store import Store


def test_is_analysis_type_eligible_for_observations_upload_eligible_wgs(
    case_id: str, balsamic_observations_api: BalsamicObservationsAPI, mocker: MockFixture
):
    """Test if the analysis type is eligible for observation uploads."""

    # GIVEN a WGS case ID and a Balsamic observations API

    # GIVEN a case with tumor samples
    mocker.patch.object(BalsamicAnalysisAPI, "is_analysis_normal_only", return_value=False)
    case: Case = balsamic_observations_api.store.get_case_by_internal_id(case_id)

    # WHEN checking analysis type eligibility for a case
    is_analysis_type_eligible_for_observations_upload: bool = (
        balsamic_observations_api.is_analysis_type_eligible_for_observations_upload(case)
    )

    # THEN the analysis type should be eligible for observation uploads
    assert is_analysis_type_eligible_for_observations_upload


def test_is_analysis_type_eligible_for_observations_upload_not_eligible_wgs(
    case_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test if the analysis type is not eligible for observation uploads."""

    # GIVEN a case ID and a Balsamic observations API

    # GIVEN a case without tumor samples (normal-only analysis)
    mocker.patch.object(BalsamicAnalysisAPI, "is_analysis_normal_only", return_value=True)
    case: Case = balsamic_observations_api.store.get_case_by_internal_id(case_id)

    # WHEN checking analysis type eligibility for a case
    is_analysis_type_eligible_for_observations_upload: bool = (
        balsamic_observations_api.is_analysis_type_eligible_for_observations_upload(case)
    )

    # THEN the analysis type should not be eligible for observation uploads
    assert not is_analysis_type_eligible_for_observations_upload
    assert (
        f"Normal only analysis {case.internal_id} is not supported for WGS Loqusdb uploads"
        in caplog.text
    )


def test_is_analysis_type_eligible_for_observations_eligible_tgs(cg_context: CGConfig):
    # GIVEN a Balsamic Observations API
    balsamic_observations_api = BalsamicObservationsAPI(config=cg_context)

    # GIVEN a TGS case with a panel that allows for LoqusDB uploads and only one sample
    case: Case = create_autospec(
        Case,
        internal_id="balsamic_tgs_case",
        samples=[
            create_autospec(
                Sample,
                capture_kit="GMSmyeloid",
                prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
            )
        ],
    )

    # WHEN checking analysis type eligibility for a case
    is_eligible: bool = balsamic_observations_api.is_analysis_type_eligible_for_observations_upload(
        case
    )

    # THEN the analysis type should be eligible for observation uploads
    assert is_eligible


def test_is_analysis_type_eligible_for_observations_not_eligible_tgs(cg_context: CGConfig):
    # GIVEN a Balsamic Observations API
    balsamic_observations_api = BalsamicObservationsAPI(config=cg_context)

    # GIVEN a TGS case with a panel that allows for LoqusDB uploads and two samples
    sample = create_autospec(
        Sample,
        capture_kit="GMSmyeloid",
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    case: Case = create_autospec(
        Case,
        internal_id="balsamic_tgs_case",
        samples=[sample, sample],
    )

    # WHEN checking analysis type eligibility for a case
    is_eligible: bool = balsamic_observations_api.is_analysis_type_eligible_for_observations_upload(
        case
    )

    # THEN the analysis type should not be eligible for observation uploads
    assert not is_eligible


@pytest.mark.parametrize(
    "bed_name, is_allowed", [("GMSmyeloid", True), ("Not valid bed name", False)]
)
def test_is_panel_allowed_for_observations_upload_bed_name(
    cg_context: CGConfig, bed_name: str, is_allowed: bool
):
    # GIVEN a Balsamic observations API
    balsamic_observations_api = BalsamicObservationsAPI(config=cg_context)
    balsamic_observations_api.lims_api = Mock()

    # GIVEN a store
    store: Store = create_autospec(Store)

    # GIVEN a case that needs a panel to be uploaded to LoqusDB
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_id",
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    case: Case = create_autospec(Case, internal_id="case_id", samples=[sample])
    bed: Bed = create_autospec(Bed)
    bed.name = bed_name
    store.get_bed_version_by_short_name = Mock(return_value=create_autospec(BedVersion, bed=bed))
    balsamic_observations_api.store = store

    # WHEN calling is_panel_allowed_for_observations_upload
    is_panel_allowed: bool = balsamic_observations_api.is_panel_allowed_for_observations_upload(
        case
    )

    # THEN result is as expected
    assert is_panel_allowed == is_allowed


def test_is_panel_allowed_for_upload_WGS(cg_context: CGConfig):
    # GIVEN a Balsamic observations API
    balsamic_observations_api = BalsamicObservationsAPI(config=cg_context)
    balsamic_observations_api.lims_api = Mock()

    # GIVEN a store
    store: Store = create_autospec(Store)

    # GIVEN a case that does not need a panel to be uploaded to LoqusDB
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_id",
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )
    case: Case = create_autospec(Case, internal_id="case_id", samples=[sample])
    balsamic_observations_api.store = store

    # WHEN calling is_panel_allowed_for_observations_upload
    is_panel_allowed: bool = balsamic_observations_api.is_panel_allowed_for_observations_upload(
        case
    )

    # THEN the result should be true
    assert is_panel_allowed


def test_is_panel_allowed_no_bed_version(cg_context: CGConfig):
    # GIVEN a Balsamic observations API
    balsamic_observations_api = BalsamicObservationsAPI(config=cg_context)
    balsamic_observations_api.lims_api = Mock()

    # GIVEN a store
    store: Store = create_autospec(Store)

    # GIVEN a case that needs a panel to be uploaded to LoqusDB
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_id",
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    case: Case = create_autospec(Case, internal_id="case_id", samples=[sample])

    # GIVEN that the LIMS short name does not match any bed versions
    store.get_bed_version_by_short_name = Mock(return_value=None)
    balsamic_observations_api.store = store

    # WHEN calling is_panel_allowed_for_observations_upload
    is_panel_allowed: bool = balsamic_observations_api.is_panel_allowed_for_observations_upload(
        case
    )

    # THEN the result should be false
    assert not is_panel_allowed


def test_is_case_eligible_for_observations_upload(
    case_id: str, balsamic_observations_api: BalsamicObservationsAPI, mocker: MockFixture
):
    """Test whether a case is eligible for Balsamic observation uploads."""

    # GIVEN a case and a Balsamic observations API
    case: Case = balsamic_observations_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN an eligible sequencing method and a case with tumor samples
    mocker.patch.object(
        BalsamicAnalysisAPI, "get_data_analysis_type", return_value=CancerAnalysisType.TUMOR_WGS
    )
    mocker.patch.object(BalsamicAnalysisAPI, "is_analysis_normal_only", return_value=False)

    # WHEN checking the upload eligibility for a case
    is_case_eligible_for_observations_upload: bool = (
        balsamic_observations_api.is_case_eligible_for_observations_upload(case)
    )

    # THEN the case should be eligible for observation uploads
    assert is_case_eligible_for_observations_upload


def test_is_case_not_eligible_for_observations_upload(
    case_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test whether a case is eligible for Balsamic observation uploads."""

    # GIVEN a case and a Balsamic observations API
    case: Case = balsamic_observations_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a case with an invalid sequencing type
    mocker.patch.object(BalsamicAnalysisAPI, "is_analysis_normal_only", return_value=False)
    mocker.patch.object(
        BalsamicAnalysisAPI,
        "get_data_analysis_type",
        return_value=CancerAnalysisType.TUMOR_NORMAL_PANEL,
    )

    # WHEN checking the upload eligibility for a case
    is_case_eligible_for_observations_upload: bool = (
        balsamic_observations_api.is_case_eligible_for_observations_upload(case)
    )

    # THEN the case should not be eligible for observation uploads
    assert not is_case_eligible_for_observations_upload


def test_load_observations(
    case_id: str,
    loqusdb_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    balsamic_observations_input_files: BalsamicObservationsInputFiles,
    number_of_loaded_variants: int,
    caplog: LogCaptureFixture,
    mocker: MockFixture,
):
    """Test loading of Balsamic case observations."""
    caplog.set_level(logging.DEBUG)

    # GIVEN an observations API and a list of input files for upload
    case: Case = balsamic_observations_api.store.get_case_by_internal_id(case_id)
    mocker.patch.object(
        BalsamicObservationsAPI,
        "get_observations_input_files",
        return_value=balsamic_observations_input_files,
    )

    # GIVEN an observations API mocked scenario
    mocker.patch.object(BalsamicObservationsAPI, "is_duplicate", return_value=False)

    # WHEN loading the case to Loqusdb
    balsamic_observations_api.load_observations(case)

    # THEN the observations should be loaded successfully
    assert f"Uploaded {number_of_loaded_variants} variants to Loqusdb" in caplog.text


def test_load_duplicated_observations(
    case_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    caplog: LogCaptureFixture,
    mocker: MockFixture,
):
    """Test raise of a duplicate exception when loading Balsamic case observations."""
    caplog.set_level(logging.DEBUG)

    # GIVEN an observations API and a Balsamic case
    case: Case = balsamic_observations_api.store.get_case_by_internal_id(case_id)

    # GIVEN a duplicate case in Loqusdb
    mocker.patch.object(BalsamicObservationsAPI, "is_duplicate", return_value=True)

    # WHEN loading the case to Loqusdb
    with pytest.raises(LoqusdbDuplicateRecordError):
        balsamic_observations_api.load_observations(case)

    # THEN the observations upload should be aborted
    assert f"Case {case_id} has already been uploaded to Loqusdb" in caplog.text


def test_load_cancer_observations(
    case_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    balsamic_observations_input_files: BalsamicObservationsInputFiles,
    number_of_loaded_variants: int,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test loading of cancer case observations for Balsamic."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a Balsamic observations API, a list of input files, and a cancer case
    case: Case = balsamic_observations_api.store.get_case_by_internal_id(case_id)

    # GIVEN an observations API mocked scenario
    mocker.patch.object(
        BalsamicAnalysisAPI,
        "get_data_analysis_type",
        return_value=CancerAnalysisType.TUMOR_NORMAL_WGS,
    )

    # WHEN loading the case to a somatic Loqusdb instance
    balsamic_observations_api.load_cancer_observations(
        case=case,
        input_files=balsamic_observations_input_files,
        loqusdb_api=balsamic_observations_api.loqusdb_somatic_api,
    )

    # THEN the observations should be loaded successfully
    assert f"Uploaded {number_of_loaded_variants} variants to Loqusdb" in caplog.text


@pytest.mark.parametrize(
    "prep_category, panel, loqusdb_instance",
    [
        (
            SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
            BalsamicObservationPanel.EXOME,
            LoqusdbInstance.SOMATIC_EXOME,
        ),
        (
            SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
            BalsamicObservationPanel.LYMPHOID,
            LoqusdbInstance.SOMATIC_LYMPHOID,
        ),
        (
            SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
            BalsamicObservationPanel.MYELOID,
            LoqusdbInstance.SOMATIC_MYELOID,
        ),
    ],
    ids=["Exome", "Lymphoid", "Myeloid"],
)
def test_panel_upload(
    prep_category: SeqLibraryPrepCategory,
    panel: BalsamicObservationPanel,
    loqusdb_instance: LoqusdbInstance,
    mocker: MockerFixture,
):

    # GIVEN that a known panel is set in LIMS
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.capture_kit = Mock(return_value="file.bed")
    lims_api.get_source = Mock(return_value="Not valid")

    # GIVEN a store
    store_session = create_autospec(Session)
    store: Store = create_autospec(Store, session=store_session)
    bed = create_autospec(Bed)
    bed.name = panel
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, bed=bed, filename="file.bed")
    )
    store.get_bed_version_by_short_name = Mock(
        return_value=create_autospec(BedVersion, bed=bed, filename="file.bed")
    )

    # GIVEN a panel case with a TGS sample
    customer = create_autospec(Customer, internal_id=CustomerId.CUST110)
    sample: Sample = create_autospec(Sample, prep_category=prep_category, loqusdb_id=None)
    case: Case = create_autospec(
        Case,
        internal_id="case_id",
        samples=[sample],
        loqusdb_uploaded_samples=[],
        customer=customer,
    )
    store.get_case_by_internal_id = Mock(return_value=case)
    store.get_sample_ids_by_case_id = Mock(return_value=[sample])

    # GIVEN balsamic observations API
    balsamic_observations_api = BalsamicObservationsAPI(
        create_autospec(
            CGConfig,
            lims_api=lims_api,
            balsamic=Mock(),
            loqusdb=Mock(),
            loqusdb_rd_lwp=Mock(),
            loqusdb_wes=Mock(),
            loqusdb_somatic=Mock(),
            loqusdb_tumor=Mock(),
            loqusdb_somatic_lymphoid=Mock(),
            loqusdb_somatic_myeloid=Mock(),
            loqusdb_somatic_exome=Mock(),
            run_instruments=create_autospec(
                RunInstruments,
                illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="runs_dir"),
            ),
            sentieon_licence_server=Mock(),
            status_db=store,
        ),
    )

    loqusdb_selection = mocker.spy(ObservationsAPI, "get_loqusdb_api")
    loqusdb_load = mocker.patch.object(LoqusdbAPI, "load")
    mocker.patch.object(LoqusdbAPI, "get_case", side_effect=[None, {LOQUSDB_ID: 1}])
    mocker.patch.object(LoqusdbAPI, "get_duplicate", return_value=None)
    path_to_snv_file = Path("snv/vcf/path")
    mocker.patch.object(
        BalsamicObservationsAPI,
        "get_observations_files_from_hk",
        return_value=create_autospec(BalsamicObservationsInputFiles, snv_vcf_path=path_to_snv_file),
    )

    # WHEN uploading
    balsamic_observations_api.upload(case.internal_id)

    # THEN the correct loqusDB instance is selected
    loqusdb_selection.assert_called_once_with(ANY, loqusdb_instance)

    # THEN the case is uploaded
    loqusdb_load.assert_called_once_with(
        case_id=case.internal_id,
        snv_vcf_path=path_to_snv_file,
    )

    # THEN the loqusdb id has been set
    assert all(sample.loqusdb_id for sample in case.samples)

    # THEN the ids should have been commited
    store_session.commit.assert_called_once()

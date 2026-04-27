"""Test RAREDISEASE observations API."""

import logging
from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import RarediseaseLoadParameters
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import LoqusdbDuplicateRecordError
from cg.meta.observations import raredisease_observations_api as raredisease
from cg.meta.observations.raredisease_observations_api import RarediseaseObservationsAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig, CommonAppConfig, RarediseaseConfig, RunInstruments
from cg.models.observations.input_files import RarediseaseObservationsInputFiles
from cg.store.models import Case


def test_is_sample_type_eligible_for_observations_upload(
    case_id: str, raredisease_observations_api: RarediseaseObservationsAPI
):
    """Test if the sample type is eligible for observation uploads."""
    # GIVEN a case without tumor samples and a RAREDISEASE observations API
    case: Case = raredisease_observations_api.store.get_case_by_internal_id(case_id)

    # WHEN checking sample type eligibility for a case
    is_sample_type_eligible_for_observations_upload: bool = (
        raredisease_observations_api.is_sample_type_eligible_for_observations_upload(case)
    )

    # THEN the analysis type should be eligible for observation uploads
    assert is_sample_type_eligible_for_observations_upload


def test_is_sample_type_not_eligible_for_observations_upload(
    case_id: str, raredisease_observations_api: RarediseaseObservationsAPI
):
    """Test if the sample type is not eligible for observation uploads."""

    # GIVEN a case with tumor samples and a RAREDISEASE observations API
    case: Case = raredisease_observations_api.store.get_case_by_internal_id(case_id)
    case.samples[0].is_tumour = True

    # WHEN checking sample type eligibility for a case
    is_sample_type_eligible_for_observations_upload: bool = (
        raredisease_observations_api.is_sample_type_eligible_for_observations_upload(case)
    )

    # THEN the analysis type should not be eligible for observation uploads
    assert not is_sample_type_eligible_for_observations_upload


def test_is_case_eligible_for_observations_upload(
    case_id: str, raredisease_observations_api: RarediseaseObservationsAPI, mocker: MockFixture
):
    """Test whether a case is eligible for RAREDISEASE observation uploads."""

    # GIVEN a case and a RAREDISEASE observations API
    case: Case = raredisease_observations_api.analysis_api.status_db.get_case_by_internal_id(
        case_id
    )

    # GIVEN a RAREDISEASE scenario for Loqusdb uploads
    mocker.patch.object(
        RarediseaseAnalysisAPI,
        "get_data_analysis_type",
        return_value=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )

    # WHEN checking the upload eligibility for a case
    is_case_eligible_for_observations_upload: bool = (
        raredisease_observations_api.is_case_eligible_for_observations_upload(case)
    )

    # THEN the case should be eligible for observation uploads
    assert is_case_eligible_for_observations_upload


def test_is_case_not_eligible_for_observations_upload(
    case_id: str, raredisease_observations_api: RarediseaseObservationsAPI, mocker: MockFixture
):
    """Test whether a case is not eligible for RAREDISEASE observation uploads."""

    # GIVEN a case and a RAREDISEASE observations API
    case: Case = raredisease_observations_api.analysis_api.status_db.get_case_by_internal_id(
        case_id
    )

    # GIVEN a RAREDISEASE scenario for Loqusdb uploads with an invalid sequencing method
    mocker.patch.object(
        RarediseaseAnalysisAPI,
        "get_data_analysis_type",
        return_value=SeqLibraryPrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING,
    )

    # WHEN checking the upload eligibility for a case
    is_case_eligible_for_observations_upload: bool = (
        raredisease_observations_api.is_case_eligible_for_observations_upload(case)
    )

    # THEN the case should not be eligible for observation uploads
    assert not is_case_eligible_for_observations_upload


def test_load_observations(
    case_id: str,
    loqusdb_id: str,
    number_of_loaded_variants: int,
    raredisease_observations_api: RarediseaseObservationsAPI,
    raredisease_observations_input_files: RarediseaseObservationsInputFiles,
    caplog: LogCaptureFixture,
    mocker: MockFixture,
):
    """Test loading of case observations for RAREDISEASE."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a RAREDISEASE observations API and a list of observations input files

    # GIVEN a RAREDISEASE case and a mocked scenario for uploads
    case: Case = raredisease_observations_api.store.get_case_by_internal_id(case_id)
    mocker.patch.object(
        RarediseaseAnalysisAPI,
        "get_data_analysis_type",
        return_value=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )
    mocker.patch.object(
        RarediseaseObservationsAPI,
        "get_observations_input_files",
        return_value=raredisease_observations_input_files,
    )
    mocker.patch.object(RarediseaseObservationsAPI, "is_duplicate", return_value=False)

    # WHEN loading the case to Loqusdb
    raredisease_observations_api.load_observations(case)

    # THEN the observations should be loaded without any errors
    assert f"Uploaded {number_of_loaded_variants} variants to Loqusdb" in caplog.text


def test_load_observations_success(
    raredisease_config_object: RarediseaseConfig,
    run_instruments_config: RunInstruments,
    mocker: MockFixture,
):
    """Test successful loading of case observations for raredisease."""

    # GIVEN a RarediseaseAnalysisAPI with a valid sequencing method for Loqusdb uploads
    analysis_api: RarediseaseAnalysisAPI = create_autospec(RarediseaseAnalysisAPI)
    analysis_api.get_data_analysis_type = Mock(return_value="wgs")
    mocker.patch.object(
        raredisease,
        "RarediseaseAnalysisAPI",
        return_value=analysis_api,
    )

    # GIVEN a CGConfig with the necessary fields to load observations for raredisease
    cg_config: CGConfig = create_autospec(
        CGConfig,
        loqusdb=create_autospec(
            CommonAppConfig,
            binary_path="path/to/loqusdb_binary",
            config_path="path/to/loqusdb_config",
        ),
        loqusdb_rd_lwp="",
        loqusdb_wes="",
        loqusdb_somatic="",
        loqusdb_tumor="",
        loqusdb_somatic_lymphoid="",
        loqusdb_somatic_myeloid="",
        loqusdb_somatic_exome="",
        raredisease=raredisease_config_object,
        run_instruments=run_instruments_config,
        tower_binary_path="path/to/tower_binary",
    )

    # GIVEN a raredisease observations API with a Loqusdb API and observations input files
    observation_api = RarediseaseObservationsAPI(config=cg_config)

    loqus_db_api: LoqusdbAPI = create_autospec(LoqusdbAPI)
    load_mock = mocker.patch.object(loqus_db_api, "load")
    observation_api.get_loqusdb_api = Mock(return_value=loqus_db_api)

    observation_files: RarediseaseObservationsInputFiles = create_autospec(
        RarediseaseObservationsInputFiles,
        profile_vcf_path=Path("path/to/profile.vcf"),
        snv_vcf_path=Path("path/to/snv.vcf"),
        sv_vcf_path=Path("path/to/sv.vcf"),
        family_ped_path=Path("path/to/family.ped"),
    )
    observation_api.get_observations_input_files = Mock(return_value=observation_files)
    observation_api.is_duplicate = Mock(return_value=False)

    # GIVEN a case eligible for observations upload
    case: Case = create_autospec(Case, internal_id="case_id")

    # WHEN loading the case to Loqusdb
    observation_api.load_observations(case)

    # THEN the loqusdb call should have been as expected
    load_mock.assert_called_once_with(
        case_id=case.internal_id,
        snv_vcf_path=observation_files.snv_vcf_path,
        sv_vcf_path=observation_files.sv_vcf_path,
        profile_vcf_path=observation_files.profile_vcf_path,
        family_ped_path=observation_files.family_ped_path,
        gq_threshold=RarediseaseLoadParameters.GQ_THRESHOLD.value,
        hard_threshold=RarediseaseLoadParameters.HARD_THRESHOLD.value,
        soft_threshold=RarediseaseLoadParameters.SOFT_THRESHOLD.value,
        loqusdb_options=["--keep-chr-prefix", "--genome-build", "GRCh38"],
    )


def test_load_duplicated_observations(
    case_id: str,
    loqusdb_id: str,
    number_of_loaded_variants: int,
    raredisease_observations_api: RarediseaseObservationsAPI,
    raredisease_observations_input_files: RarediseaseObservationsInputFiles,
    caplog: LogCaptureFixture,
    mocker: MockFixture,
):
    """Test loading of duplicated observations for RAREDISEASE."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a RAREDISEASE observations API and a list of observations input files

    # GIVEN a RAREDISEASE case and a mocked scenario for uploads with a case already uploaded
    case: Case = raredisease_observations_api.store.get_case_by_internal_id(case_id)
    mocker.patch.object(
        RarediseaseAnalysisAPI,
        "get_data_analysis_type",
        return_value=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )
    mocker.patch.object(
        RarediseaseObservationsAPI,
        "get_observations_input_files",
        return_value=raredisease_observations_input_files,
    )
    mocker.patch.object(RarediseaseObservationsAPI, "is_duplicate", return_value=True)

    # WHEN loading the case to Loqusdb
    with pytest.raises(LoqusdbDuplicateRecordError):
        raredisease_observations_api.load_observations(case)

    # THEN the observations upload should be aborted
    assert f"Case {case_id} has already been uploaded to Loqusdb" in caplog.text

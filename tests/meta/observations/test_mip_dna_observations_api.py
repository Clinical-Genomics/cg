"""Test MIP-DNA observations API."""

import logging

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from cg.constants.sequencing import SequencingMethod
from cg.exc import LoqusdbDuplicateRecordError
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.observations.input_files import MipDNAObservationsInputFiles
from cg.store.models import Case


def test_is_sample_type_eligible_for_observations_upload(
    case_id: str, mip_dna_observations_api: MipDNAObservationsAPI
):
    """Test if the sample type is eligible for observation uploads."""

    # GIVEN a case without tumor samples and a MIP-DNA observations API
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(case_id)

    # WHEN checking sample type eligibility for a case
    is_sample_type_eligible_for_observations_upload: bool = (
        mip_dna_observations_api.is_sample_type_eligible_for_observations_upload(case)
    )

    # THEN the analysis type should be eligible for observation uploads
    assert is_sample_type_eligible_for_observations_upload


def test_is_sample_type_not_eligible_for_observations_upload(
    case_id: str, mip_dna_observations_api: MipDNAObservationsAPI
):
    """Test if the sample type is not eligible for observation uploads."""

    # GIVEN a case with tumor samples and a MIP-DNA observations API
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(case_id)
    case.samples[0].is_tumour = True

    # WHEN checking sample type eligibility for a case
    is_sample_type_eligible_for_observations_upload: bool = (
        mip_dna_observations_api.is_sample_type_eligible_for_observations_upload(case)
    )

    # THEN the analysis type should not be eligible for observation uploads
    assert not is_sample_type_eligible_for_observations_upload


def test_is_case_eligible_for_observations_upload(
    case_id: str, mip_dna_observations_api: MipDNAObservationsAPI, mocker: MockFixture
):
    """Test whether a case is eligible for MIP-DNA observation uploads."""

    # GIVEN a case and a MIP-DNA observations API
    case: Case = mip_dna_observations_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a MIP-DNA scenario for Loqusdb uploads
    mocker.patch.object(
        MipDNAAnalysisAPI, "get_data_analysis_type", return_value=SequencingMethod.WGS
    )

    # WHEN checking the upload eligibility for a case
    is_case_eligible_for_observations_upload: bool = (
        mip_dna_observations_api.is_case_eligible_for_observations_upload(case)
    )

    # THEN the case should be eligible for observation uploads
    assert is_case_eligible_for_observations_upload


def test_is_case_not_eligible_for_observations_upload(
    case_id: str, mip_dna_observations_api: MipDNAObservationsAPI, mocker: MockFixture
):
    """Test whether a case is not eligible for MIP-DNA observation uploads."""

    # GIVEN a case and a MIP-DNA observations API
    case: Case = mip_dna_observations_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a MIP-DNA scenario for Loqusdb uploads with an invalid sequencing method
    mocker.patch.object(
        MipDNAAnalysisAPI, "get_data_analysis_type", return_value=SequencingMethod.WTS
    )

    # WHEN checking the upload eligibility for a case
    is_case_eligible_for_observations_upload: bool = (
        mip_dna_observations_api.is_case_eligible_for_observations_upload(case)
    )

    # THEN the case should not be eligible for observation uploads
    assert not is_case_eligible_for_observations_upload


def test_load_observations(
    case_id: str,
    loqusdb_id: str,
    number_of_loaded_variants: int,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mip_dna_observations_input_files: MipDNAObservationsInputFiles,
    caplog: LogCaptureFixture,
    mocker: MockFixture,
):
    """Test loading of case observations for MIP-DNA."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a MIP-DNA observations API and a list of observations input files

    # GIVEN a MIP-DNA case and a mocked scenario for uploads
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(case_id)
    mocker.patch.object(
        MipDNAAnalysisAPI, "get_data_analysis_type", return_value=SequencingMethod.WGS
    )
    mocker.patch.object(
        MipDNAObservationsAPI,
        "get_observations_input_files",
        return_value=mip_dna_observations_input_files,
    )
    mocker.patch.object(MipDNAObservationsAPI, "is_duplicate", return_value=False)

    # WHEN loading the case to Loqusdb
    mip_dna_observations_api.load_observations(case)

    # THEN the observations should be loaded without any errors
    assert f"Uploaded {number_of_loaded_variants} variants to Loqusdb" in caplog.text


def test_load_duplicated_observations(
    case_id: str,
    loqusdb_id: str,
    number_of_loaded_variants: int,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mip_dna_observations_input_files: MipDNAObservationsInputFiles,
    caplog: LogCaptureFixture,
    mocker: MockFixture,
):
    """Test loading of duplicated observations for MIP-DNA."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a MIP-DNA observations API and a list of observations input files

    # GIVEN a MIP-DNA case and a mocked scenario for uploads with a case already uploaded
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(case_id)
    mocker.patch.object(
        MipDNAAnalysisAPI, "get_data_analysis_type", return_value=SequencingMethod.WGS
    )
    mocker.patch.object(
        MipDNAObservationsAPI,
        "get_observations_input_files",
        return_value=mip_dna_observations_input_files,
    )
    mocker.patch.object(MipDNAObservationsAPI, "is_duplicate", return_value=True)

    # WHEN loading the case to Loqusdb
    with pytest.raises(LoqusdbDuplicateRecordError):
        mip_dna_observations_api.load_observations(case)

    # THEN the observations upload should be aborted
    assert f"Case {case_id} has already been uploaded to Loqusdb" in caplog.text

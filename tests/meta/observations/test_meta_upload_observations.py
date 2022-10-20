"""Test observations API methods."""

import logging
from typing import List

import pytest
from _pytest.logging import LogCaptureFixture

from cg.apps.loqus import LoqusdbAPI
from cg.constants.sequencing import SequencingMethod
from cg.exc import LoqusdbDuplicateRecordError, LoqusdbUploadCaseError
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.observations.input_files import MipDNAObservationsInputFiles
from cg.store import models, Store
from tests.meta.observations.conftest import (
    MockLoqusdbAPI,
    MockMipDNAObservationsAPI,
    MockMipDNAObservationsAPIDuplicateCase,
)


def test_observations_upload(
    case_id: str,
    loqusdb_config_path: str,
    mock_mip_dna_observations_api: MockMipDNAObservationsAPI,
    analysis_store: Store,
    caplog: LogCaptureFixture,
):
    """Test upload observations method."""
    caplog.set_level(logging.DEBUG)

    # GIVEN an observations API and a case object
    case: models.Family = analysis_store.family(case_id)

    # WHEN uploading the case observations to Loqusdb
    mock_mip_dna_observations_api.upload(case)

    # THEN the case should be successfully uploaded
    assert f"Uploaded 15 variants to Loqusdb" in caplog.text


def test_observations_upload_duplicate(
    case_id: str,
    loqusdb_config_path: str,
    mock_mip_dna_observations_api_duplicate_case: MockMipDNAObservationsAPIDuplicateCase,
    analysis_store: Store,
    caplog: LogCaptureFixture,
):
    """Test upload observations method."""
    caplog.set_level(logging.DEBUG)

    # GIVEN an observations API and a case object that has already been uploaded to Loqusdb
    case: models.Family = analysis_store.family(case_id)

    # WHEN uploading the case observations to Loqusdb
    with pytest.raises(LoqusdbDuplicateRecordError):
        # THEN a duplicate record error should be raised
        mock_mip_dna_observations_api_duplicate_case.upload(case)

    assert f"Case {case.internal_id} has been already uploaded to Loqusdb" in caplog.text


def test_mip_dna_load_observations(
    case_id: str,
    loqusdb_config_path: str,
    mock_loqusdb_api: MockLoqusdbAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    mock_mip_dna_observations_api: MockMipDNAObservationsAPI,
    analysis_store: Store,
    caplog: LogCaptureFixture,
):
    """Test loading of case observations for rare disease."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a mock MIP DNA observations API, an empty Loqusdb API and a list of observations input files
    case: models.Family = analysis_store.family(case_id)

    # WHEN loading the case to Loqusdb
    mock_mip_dna_observations_api.load_observations(
        case, mock_loqusdb_api, observations_input_files
    )

    # THEN the observations should be loaded without any errors
    assert f"Uploaded 15 variants to Loqusdb" in caplog.text


def test_mip_dna_get_loqusdb_api(
    case_id: str,
    loqusdb_binary_path: str,
    loqusdb_config_path: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    analysis_store: Store,
):
    """Test getting Loqusdb API given a case object."""

    # GIVEN a MIP DNA observations API and a case object
    case: models.Family = analysis_store.family(case_id)

    # WHEN getting the Loqusdb API
    loqusdb_api: LoqusdbAPI = mip_dna_observations_api.get_loqusdb_api(case)

    # THEN a WGS MIP DNA Loqusdb API should be returned
    assert isinstance(loqusdb_api, LoqusdbAPI)
    assert loqusdb_api.binary_path == loqusdb_binary_path
    assert loqusdb_api.config_path == loqusdb_config_path


def test_mip_dna_get_loqusdb_api_tumor_case(
    case_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    analysis_store: Store,
    caplog: LogCaptureFixture,
):
    """Test getting the Loqusdb API for a case with tumour samples."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a MIP DNA observations API and a case object with a tumour sample
    case: models.Family = analysis_store.family(case_id)
    case.links[0].sample.is_tumour = True

    # WHEN getting the Loqusdb API
    with pytest.raises(LoqusdbUploadCaseError):
        # THEN a data integrity error should be raised and the execution aborted
        mip_dna_observations_api.get_loqusdb_api(case)

    assert f"Case {case.internal_id} has tumour samples. Cancelling its upload." in caplog.text


def test_mip_dna_is_duplicate(
    case_id: str,
    loqusdb_api: LoqusdbAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    mip_dna_observations_api: MipDNAObservationsAPI,
    analysis_store: Store,
):
    """Test duplicate extraction for a case that is not Loqusdb."""

    # GIVEN a Loqusdb instance with no case duplicates
    case: models.Family = analysis_store.family(case_id)

    # WHEN checking that a case has not been uploaded to Loqusdb
    is_duplicate: bool = mip_dna_observations_api.is_duplicate(
        case,
        loqusdb_api,
        observations_input_files,
    )

    # THEN there should be no duplicates in Loqusdb
    assert is_duplicate is False


def test_mip_dna_is_duplicate_case_output(
    case_id: str,
    loqusdb_api: LoqusdbAPI,
    loqusdb_case_output: bytes,
    observations_input_files: MipDNAObservationsInputFiles,
    mip_dna_observations_api: MipDNAObservationsAPI,
    analysis_store: Store,
):
    """Test duplicate extraction for a case that already exists in Loqusdb."""

    # GIVEN a Loqusdb instance with a duplicated case
    case: models.Family = analysis_store.family(case_id)
    loqusdb_api.process.stdout = loqusdb_case_output.decode("utf-8")

    # WHEN checking that a case has been already uploaded to Loqusdb
    is_duplicate: bool = mip_dna_observations_api.is_duplicate(
        case, loqusdb_api, observations_input_files
    )

    # THEN an upload of a duplicate case should be detected
    assert is_duplicate is True


def test_mip_dna_is_duplicate_loqusdb_id(
    case_id: str,
    loqusdb_id: str,
    loqusdb_api: LoqusdbAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    mip_dna_observations_api: MipDNAObservationsAPI,
    analysis_store: Store,
):
    """Test duplicate extraction for a case that already exists in Loqusdb."""

    # GIVEN a Loqusdb instance with a duplicated case and whose samples already have a Loqusdb ID
    case: models.Family = analysis_store.family(case_id)
    case.links[0].sample.loqusdb_id = loqusdb_id

    # WHEN checking that the sample observations have already been uploaded
    is_duplicate: bool = mip_dna_observations_api.is_duplicate(
        case, loqusdb_api, observations_input_files
    )

    # THEN a duplicated upload should be identified
    assert is_duplicate is True


def test_mip_dna_get_supported_sequencing_methods(mip_dna_observations_api: MipDNAObservationsAPI):
    """Test get_supported_sequencing methods."""

    # GIVEN a MIP DNA observations API

    # WHEN retrieving the rare disease sequencing methods
    sequencing_methods: List[
        SequencingMethod
    ] = mip_dna_observations_api.get_supported_sequencing_methods()

    # WHEN retrieving the supported analysis
    assert len(sequencing_methods) == 2
    assert SequencingMethod.WGS in sequencing_methods
    assert SequencingMethod.WES in sequencing_methods

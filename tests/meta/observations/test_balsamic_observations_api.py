"""Test Balsamic observations API."""

import logging

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from cg.constants.constants import CancerAnalysisType
from cg.exc import LoqusdbDuplicateRecordError
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.observations.input_files import BalsamicObservationsInputFiles
from cg.store.models import Case


def test_is_analysis_type_eligible_for_observations_upload(
    case_id: str, balsamic_observations_api: BalsamicObservationsAPI, mocker: MockFixture
):
    """Test if the analysis type is eligible for observation uploads."""

    # GIVEN a case ID and a Balsamic observations API

    # GIVEN a case with tumor samples
    mocker.patch.object(BalsamicAnalysisAPI, "is_analysis_normal_only", return_value=False)

    # WHEN checking analysis type eligibility for a case
    is_analysis_type_eligible_for_observations_upload: bool = (
        balsamic_observations_api.is_analysis_type_eligible_for_observations_upload(case_id)
    )

    # THEN the analysis type should be eligible for observation uploads
    assert is_analysis_type_eligible_for_observations_upload


def test_is_analysis_type_not_eligible_for_observations_upload(
    case_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test if the analysis type is not eligible for observation uploads."""

    # GIVEN a case ID and a Balsamic observations API

    # GIVEN a case without tumor samples (normal-only analysis)
    mocker.patch.object(BalsamicAnalysisAPI, "is_analysis_normal_only", return_value=True)

    # WHEN checking analysis type eligibility for a case
    is_analysis_type_eligible_for_observations_upload: bool = (
        balsamic_observations_api.is_analysis_type_eligible_for_observations_upload(case_id)
    )

    # THEN the analysis type should not be eligible for observation uploads
    assert not is_analysis_type_eligible_for_observations_upload
    assert f"Normal only analysis {case_id} is not supported for Loqusdb uploads" in caplog.text


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

    # GIVEN a case with tumor sample and an invalid sequencing type
    mocker.patch.object(BalsamicAnalysisAPI, "is_analysis_normal_only", return_value=False)
    mocker.patch.object(
        BalsamicAnalysisAPI, "get_data_analysis_type", return_value=CancerAnalysisType.TUMOR_PANEL
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

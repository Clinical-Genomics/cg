""" Tests for Loqusdb API."""

import logging
from subprocess import CalledProcessError

import pytest
from _pytest.logging import LogCaptureFixture

from cg.apps.loqus import LoqusdbAPI
from cg.constants.constants import FileFormat
from cg.constants.observations import MipDNALoadParameters
from cg.exc import CaseNotFoundError
from cg.io.controller import ReadStream
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import MipDNAObservationsInputFiles


def test_instantiate(cg_config_locusdb: CGConfig):
    """Test instantiation of Loqusdb API."""

    # GIVEN a Loqusdb binary and config paths
    binary_path: str = cg_config_locusdb.loqusdb.binary_path
    config_path: str = cg_config_locusdb.loqusdb.config_path

    # WHEN instantiating a Loqusdb api
    loqusdb_api = LoqusdbAPI(binary_path=binary_path, config_path=config_path)

    # THEN assert that the API was properly initialised
    assert loqusdb_api.binary_path == binary_path
    assert loqusdb_api.config_path == config_path
    assert loqusdb_api.process


def test_load(
    case_id: str,
    loqusdb_api: LoqusdbAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    loqusdb_load_stderr: bytes,
    nr_of_loaded_variants: int,
):
    """Test loading of case to Loqusdb."""

    # GIVEN a Loqusdb API and a list of observations input files

    # WHEN uploading a case to Loqusdb
    loqusdb_api.process.stderr = loqusdb_load_stderr.decode("utf-8")
    output: dict = loqusdb_api.load(
        case_id=case_id,
        snv_vcf_path=observations_input_files.snv_vcf_path,
        sv_vcf_path=observations_input_files.sv_vcf_path,
        profile_vcf_path=observations_input_files.profile_vcf_path,
        family_ped_path=observations_input_files.family_ped_path,
        gq_threshold=MipDNALoadParameters.GQ_THRESHOLD.value,
        hard_threshold=MipDNALoadParameters.HARD_THRESHOLD.value,
        soft_threshold=MipDNALoadParameters.SOFT_THRESHOLD.value,
    )

    # THEN assert that the number of variants is the expected one
    assert output["variants"] == nr_of_loaded_variants


def test_load_parameters(
    case_id: str,
    loqusdb_api: LoqusdbAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    loqusdb_load_stderr: bytes,
    caplog: LogCaptureFixture,
):
    """Test Loqusdb load command params."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a Loqusdb API and a list of observations input files

    # WHEN uploading a case to Loqusdb
    loqusdb_api.process.stderr = loqusdb_load_stderr.decode("utf-8")
    loqusdb_api.load(
        case_id=case_id,
        snv_vcf_path=observations_input_files.snv_vcf_path,
        sv_vcf_path=observations_input_files.sv_vcf_path,
        profile_vcf_path=observations_input_files.profile_vcf_path,
        family_ped_path=observations_input_files.family_ped_path,
        gq_threshold=MipDNALoadParameters.GQ_THRESHOLD.value,
        hard_threshold=MipDNALoadParameters.HARD_THRESHOLD.value,
        soft_threshold=None,
    )

    # THEN assert that the expected params are included in the call
    assert f"--case-id {case_id}" in caplog.text
    assert f"--variant-file {observations_input_files.snv_vcf_path}" in caplog.text
    assert f"--sv-variants" not in caplog.text
    assert f"--check-profile {observations_input_files.profile_vcf_path}" in caplog.text
    assert f"--family-file {observations_input_files.family_ped_path}" in caplog.text
    assert f"--max-window" not in caplog.text
    assert f"--gq-treshold {MipDNALoadParameters.GQ_THRESHOLD.value}" in caplog.text
    assert f"--hard-threshold {MipDNALoadParameters.HARD_THRESHOLD.value}" in caplog.text
    assert f"--soft-threshold" not in caplog.text


def test_load_exception(
    case_id: str,
    loqusdb_api_exception: LoqusdbAPI,
    observations_input_files: MipDNAObservationsInputFiles,
):
    """Test Loqusdb load command with a failed output."""

    # GIVEN a Loqusdb API and a list of observations input files

    # WHEN an error occurs while loading a case

    # THEN an error should be raised
    with pytest.raises(CalledProcessError):
        loqusdb_api_exception.load(case_id, observations_input_files.snv_vcf_path)


def test_get_case(case_id: str, loqusdb_api: LoqusdbAPI, loqusdb_case_output: bytes):
    """Test get case from Loqusdb API."""

    # GIVEN a Loqusdb instance containing a case
    loqusdb_api.process.stdout = loqusdb_case_output.decode("utf-8")

    # WHEN fetching a case
    case: dict = loqusdb_api.get_case(case_id)

    # THEN assert that the correct case id is returned
    assert case["case_id"] == case_id


def test_get_case_non_existing(case_id: str, loqusdb_api: LoqusdbAPI, caplog: LogCaptureFixture):
    """Test get non existent case from Loqusdb API."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a Loqusdb instance without a case (empty output)
    loqusdb_api.process.stdout = None

    # WHEN retrieving a case
    case: dict = loqusdb_api.get_case(case_id)

    # THEN no case should be returned
    assert not case
    assert f"Case {case_id} not found in Loqusdb" in caplog.text


def test_get_duplicate(
    loqusdb_api: LoqusdbAPI,
    loqusdb_duplicate_output: bytes,
    observations_input_files: MipDNAObservationsInputFiles,
):
    """Test find matching profiles in Loqusdb."""

    # GIVEN a Loqusdb API
    loqusdb_api.process.stdout = loqusdb_duplicate_output.decode("utf-8")

    # GIVEN the expected duplicated output
    expected_duplicate: dict = ReadStream.get_content_from_stream(
        file_format=FileFormat.JSON, stream=loqusdb_duplicate_output.decode("utf-8")
    )

    # WHEN retrieving the duplicated entry
    duplicate: dict = loqusdb_api.get_duplicate(
        profile_vcf_path=observations_input_files.profile_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN assert that the duplicate individual is returned
    assert duplicate == expected_duplicate


def test_get_duplicate_non_existing(
    loqusdb_api: LoqusdbAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    caplog: LogCaptureFixture,
):
    """Test when there are no duplicates in Loqusdb."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a Loqusdb API and observations input files

    # WHEN extracting the duplicate
    duplicate: dict = loqusdb_api.get_duplicate(
        profile_vcf_path=observations_input_files.profile_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN the duplicate should be empty
    assert not duplicate
    assert (
        f"No duplicates found for profile: {observations_input_files.profile_vcf_path}"
        in caplog.text
    )


def test_delete_case(
    case_id: str, loqusdb_api: LoqusdbAPI, loqusdb_delete_stderr: bytes, caplog: LogCaptureFixture
):
    """Test case deletion from Loqusdb."""
    caplog.set_level(logging.DEBUG)

    loqusdb_api.process.stdout = loqusdb_delete_stderr.decode("utf-8")

    # GIVEN a Loqusdb API and a successful delete case output

    # WHEN deleting a case
    loqusdb_api.process.stderr = loqusdb_delete_stderr.decode("utf-8")
    loqusdb_api.delete_case(case_id)

    # THEN no errors should be raised and the case should be successfully deleted
    assert f"Removing case {case_id} from Loqusdb" in caplog.text


def test_delete_case_non_existing(
    case_id: str,
    loqusdb_api: LoqusdbAPI,
    loqusdb_delete_non_existing_stderr: bytes,
    caplog: LogCaptureFixture,
):
    """Test case deletion from Loqusdb for a not uploaded case."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a Loqusdb API and a delete non existing case output

    # WHEN deleting a case
    loqusdb_api.process.stderr = loqusdb_delete_non_existing_stderr.decode("utf-8")

    # THEN a case not found error should be raised
    with pytest.raises(CaseNotFoundError):
        loqusdb_api.delete_case(case_id)

    assert f"Case {case_id} not found in Loqusdb" in caplog.text


def test_get_nr_of_variants_in_file(
    loqusdb_api: LoqusdbAPI, loqusdb_load_stderr: bytes, nr_of_loaded_variants: int
):
    """Test getting the number of variants from a Loqusdb uploaded file."""

    # GIVEN a Loqusdb API and a successfully uploaded case
    loqusdb_api.process.stderr = loqusdb_load_stderr.decode("utf-8")

    # WHEN retrieving the number of variants
    output = loqusdb_api.get_nr_of_variants_in_file()

    # THEN assert that the number of retrieved variants is correctly retrieved
    assert output["variants"] == nr_of_loaded_variants


def test_repr_string(loqusdb_api: LoqusdbAPI, loqusdb_binary_path: str, loqusdb_config_path: str):
    """Test __repr__ of the Loqusdb API."""

    # GIVEN a Loqusdb API

    # WHEN __repr__ is called
    repr_string: str = repr(loqusdb_api)

    # THEN __repr__ should return a representation of the Loqusdb object
    assert (
        f"LoqusdbAPI(binary_path={loqusdb_binary_path}, config_path={loqusdb_config_path})"
        in repr_string
    )

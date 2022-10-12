"""
    Tests for loqusdbAPI
"""
import subprocess

import pytest
import click
from cg.apps.loqus import LoqusdbAPI
from cg.constants.constants import FileFormat
from cg.exc import CaseNotFoundError
from cg.io.controller import ReadStream
from cg.models.observations.observations_input_files import ObservationsInputFiles


def test_instantiate(loqus_config: dict):

    """Test to instantiate a loqusdb api"""
    # GIVEN a loqusdb api with some configs

    # WHEN instantiating a loqusdb api
    loqusdb = LoqusdbAPI(loqus_config)

    # THEN assert that the adapter was properly instantiated
    assert loqusdb.loqusdb_config == loqus_config["loqusdb"]["config_path"]
    assert loqusdb.loqusdb_binary == loqus_config["loqusdb"]["binary_path"]

    # WHEN instantiating with analysis_type argument as 'wes'
    loqusdb = LoqusdbAPI(loqus_config, analysis_type="wes")

    # THEN assert that the adapter was properly instantiated
    assert loqusdb.loqusdb_config == loqus_config["loqusdb_wes"]["config_path"]
    assert loqusdb.loqusdb_binary == loqus_config["loqusdb_wes"]["binary_path"]


def test_get_case(case_id, loqusdbapi, loqusdb_case_output):
    """Test to get a case via the api"""
    # GIVEN a loqusdb api
    loqusdbapi.process.stdout = loqusdb_case_output.decode("utf-8").rstrip()

    # GIVEN a case id

    # WHEN fetching a case with the adapter
    case_obj = loqusdbapi.get_case(case_id)

    # THEN assert that the correct case id is returned
    assert case_obj["case_id"] == case_id


def test_get_case_non_existing(case_id, loqusdbapi):
    """Test to get a case via the api"""
    # GIVEN a loqusdb api

    # GIVEN a case id

    # WHEN loqusdb output is empty string

    # THEN CaseNotFoundError should be raised
    with pytest.raises(CaseNotFoundError):
        loqusdbapi.get_case(case_id)


def test_get_case_command_fail(case_id: str, loqusdbapi_exception):
    """Test to see if exception is raised"""
    # GIVEN a loqusdb api
    loqusdbapi = loqusdbapi_exception

    # GIVEN a case id

    # WHEN an error occurs during fetching a case with the adapter

    # THEN assert that the error is raised
    with pytest.raises(subprocess.CalledProcessError):
        loqusdbapi.get_case(case_id)


def test_get_duplicate(
    loqusdbapi, loqusdb_duplicate_output: bytes, observation_input_files_raw: dict
):
    """Test when duplicate exists"""

    # GIVEN a loqusdb api
    loqusdbapi.process.stdout = loqusdb_duplicate_output.decode("utf-8")

    # GIVEN a duplicate output
    dup_json = ReadStream.get_content_from_stream(
        file_format=FileFormat.JSON, stream=loqusdb_duplicate_output.decode("utf-8")
    )

    # GIVEN an ObservationsInputFiles object
    files = ObservationsInputFiles(**observation_input_files_raw)

    # WHEN a duplicate exists
    duplicate = loqusdbapi.get_duplicate(files.snv_vcf)

    # THEN assert that the duplicate individual is returned
    assert dup_json == duplicate


def test_get_duplicate_non_existing(loqusdbapi, observation_input_files_raw: dict):
    """Test when no duplicate exists"""

    # GIVEN a loqusdb api

    # GIVEN an ObservationsInputFiles object
    files = ObservationsInputFiles(**observation_input_files_raw)

    # WHEN duplicate does not exist
    duplicate = loqusdbapi.get_duplicate(files.snv_vcf)

    # THEN assert that an empty dict is returned
    assert duplicate == {}


def test_load(loqusdbapi, loqusdb_output, observation_input_files_raw: dict):
    """Test to load a case"""
    # GIVEN a loqusdb api

    # GIVEN an ObservationsInputFiles object
    files = ObservationsInputFiles(**observation_input_files_raw)

    # WHEN uploading a case with 15 variants to loqusdb
    loqusdbapi.process.stderr = loqusdb_output.decode("utf-8")

    data = loqusdbapi.load(
        files.case_id, files.pedigree, files.snv_vcf, files.snv_gbcf, vcf_sv_path=files.sv_vcf
    )

    # THEN assert that the number of variants is 15
    assert data["variants"] == 15


def test_repr_string(loqus_config):

    """Test __repr__ of loqusdbAPI"""

    loqusdb = LoqusdbAPI(loqus_config)

    repr_string = repr(loqusdb)

    correct_string = (
        f"LoqusdbAPI(binary={loqus_config['loqusdb']['binary_path']},"
        f"config={loqus_config['loqusdb']['config_path']})"
    )

    assert repr_string == correct_string


def test_delete_case(case_id: str, loqusdbapi: LoqusdbAPI, loqusdb_delete_stderr: bytes):
    """Test to delete an existing case via the api."""
    # GIVEN a loqusdb api and a case_id

    # WHEN deleting an existing case from Loqusdb
    loqusdbapi.process.stderr = loqusdb_delete_stderr.decode("utf-8")
    data = loqusdbapi.delete_case(case_id)

    # THEN None should be returned and no errors raised
    assert data is None


def test_delete_case_non_existing_case(
    case_id: str, loqusdbapi: LoqusdbAPI, loqusdb_delete_nonexisting_stderr: bytes
):
    """Test to delete a non existing case via the api."""
    # GIVEN a loqusdb api and a case_id

    # WHEN deleting a non existing case from Loqusdb
    loqusdbapi.process.stderr = loqusdb_delete_nonexisting_stderr.decode("utf-8")

    # THEN assert that an error is raised
    with pytest.raises(CaseNotFoundError):
        loqusdbapi.delete_case(case_id)


def test_case_exists_true(case_id: str, loqusdbapi: LoqusdbAPI, loqusdb_case_output: bytes):
    """Test if a case exists in LoqusDB for an existing case"""
    # GIVEN a loqusdb api
    loqusdbapi.process.stdout = loqusdb_case_output.decode("utf-8").rstrip()

    # GIVEN a case id

    # WHEN fetching an existing case
    is_case = loqusdbapi.case_exists(case_id)

    # THEN assert True
    assert is_case is True


def test_case_exists_false(case_id: str, loqusdbapi: LoqusdbAPI):
    """Test if a case exists in LoqusDB for a non existing case"""
    # GIVEN a loqusdb api

    # GIVEN a case id

    # WHEN fetching a non existing case
    is_case = loqusdbapi.case_exists(case_id)

    # THEN assert False
    assert is_case is False

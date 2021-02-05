"""
    Tests for loqusdbAPI
"""

import json
import subprocess

import pytest
from cg.apps.loqus import LoqusdbAPI
from cg.exc import CaseNotFoundError


def test_instatiate(loqus_config):

    """Test to instantiate a loqusdb api"""
    # GIVEN a loqusdb api with some configs

    # WHEN instantiating a loqusdb api
    loqusdb = LoqusdbAPI(loqus_config)

    # THEN assert that the adapter was properly instantiated
    assert loqusdb.loqusdb_config == loqus_config["loqusdb"]["config_path"]
    assert loqusdb.loqusdb_binary == loqus_config["loqusdb"]["binary_path"]

    # WHEN instatiating with analysis_type argument as 'wes'
    loqusdb = LoqusdbAPI(loqus_config, analysis_type="wes")

    # THEN assert that the adapter was properly instantiated
    assert loqusdb.loqusdb_config == loqus_config["loqusdb-wes"]["config_path"]
    assert loqusdb.loqusdb_binary == loqus_config["loqusdb-wes"]["binary_path"]


def test_get_case(loqusdbapi, loqusdb_case_output):

    """Test to get a case via the api"""
    # GIVEN a loqusdb api
    case_id = "a_case"
    loqusdbapi.process.stdout = loqusdb_case_output.decode("utf-8").rstrip()
    # WHEN fetching a case with the adapter
    case_obj = loqusdbapi.get_case(case_id)
    # THEN assert that the correct case id is returned
    assert case_obj["case_id"] == case_id


def test_get_case_non_existing(loqusdbapi):

    """Test to get a case via the api"""

    # GIVEN a loqusdb api and a case id
    case_id = "a_case"

    # WHEN loqusdb output is empty string

    # THEN CaseNotFoundError should be raised
    with pytest.raises(CaseNotFoundError):
        loqusdbapi.get_case(case_id)


def test_get_case_command_fail(loqusdbapi_exception):

    """Test to see if exception is raised"""
    # GIVEN a loqusdb api and a case id
    loqusdbapi = loqusdbapi_exception
    case_id = "a_case"
    # WHEN an error occurs during fetching a case with the adapter

    # THEN assert that the error is raised
    with pytest.raises(subprocess.CalledProcessError):
        loqusdbapi.get_case(case_id)


def test_get_duplicate(loqusdbapi, loqusdb_duplicate_output):
    """Test when duplicate exists"""

    # GIVEN a loqusdb api and a duplicate output
    loqusdbapi.process.stdout = loqusdb_duplicate_output.decode("utf-8")
    dup_json = json.loads(loqusdb_duplicate_output.decode("utf-8"))

    # WHEN a duplicate exists
    duplicate = loqusdbapi.get_duplicate("vcf_path")

    # THEN assert that the duplicate individual is returned
    assert dup_json == duplicate


def test_get_duplicate_non_existing(loqusdbapi):
    """Test when no duplicate exists"""

    # GIVEN a loqusdb api

    # WHEN duplicate does not exist
    duplicate = loqusdbapi.get_duplicate("vcf_path")

    # THEN assert that an empty dict is returned
    assert duplicate == {}


def test_load(loqusdbapi, loqusdb_output):

    """Test to load a case"""
    # GIVEN a loqusdb api and some info about a case
    case_id = "test"
    ped_path = "a ped path"
    vcf_path = "a vcf path"
    vcf_sv_path = "a sv_vcf path"
    gbcf_path = "a bcf path"

    # WHEN uploading a case with 15 variants to loqusdb
    loqusdbapi.process.stderr = loqusdb_output.decode("utf-8")

    data = loqusdbapi.load(case_id, ped_path, vcf_path, vcf_sv_path, gbcf_path)

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

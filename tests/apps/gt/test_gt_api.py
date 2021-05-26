"""
    Tests for GenotypeAPI
"""

import logging

import pytest

from cg.apps.gt import GenotypeAPI
from cg.exc import CaseNotFoundError


def test_instantiate(genotype_config: dict):
    """Test to instantiate a genotype api"""
    # GIVEN a genotype api with a config

    # WHEN instantiating a genotype api
    genotype_api = GenotypeAPI(genotype_config)

    # THEN assert that the adapter was properly instantiated
    assert genotype_api.process.config == genotype_config["genotype"]["config_path"]
    assert genotype_api.process.binary == genotype_config["genotype"]["binary_path"]


def test_genotype_api_upload(genotype_api: GenotypeAPI, caplog):
    """Test to run the upload functionality in the genotype API"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a genotype api and a samples sex dictionary and a bcf_path
    sample_id = "a_sample_id"
    samples_sex = {sample_id: {"pedigree": "Female", "analysis": "Female"}}
    bcf_path = "path_to_file.bcf"

    # WHEN running the update command
    genotype_api.upload(bcf_path, samples_sex)

    # THEN assert that the correct information was communicated
    assert f"loading VCF genotypes for sample(s): {sample_id}" in caplog.text


def test_update_sample_sex(genotype_api: GenotypeAPI, caplog):
    """Test to update the sample sex function"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a sample id and a sex
    sample = "sample"
    sex = "female"

    # WHEN running the update sample sex command
    genotype_api.update_sample_sex(sample, sex)

    # THEN assert that the correct message was logged
    assert f"Set sex for sample {sample} to {sex}"


def test_update_analysis_sex(genotype_api: GenotypeAPI, caplog):
    """Test to update the sample sex function"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a sample id and a sex
    sample = "sample"
    sex = "female"

    # WHEN running the update sample sex command
    genotype_api.update_analysis_sex(sample, sex)

    # THEN assert that the correct message was logged
    assert f"Set predicted sex for sample {sample} to {sex} for the sequence analysis"


def test_export_sample(genotype_api: GenotypeAPI, genotype_export_sample_output: str, caplog):
    """Test that get_trending calls the genotype API with correct command."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a genotype api and argument days
    days = 20
    # GIVEN that the process returns some output
    genotype_api.process.stdout = genotype_export_sample_output

    # WHEN running get_trending
    genotype_api.export_sample(days=days)

    # THEN assert subprocess is running the GenotypeAPI with correct command
    call = ["config/path", "export-sample", "-d", str(days)]
    assert " ".join(call) in caplog.text


def test_export_sample_no_output(genotype_api: GenotypeAPI, caplog):
    """Test to get genotype via the api"""

    # GIVEN a genotype api
    # GIVEN a process that does not return any output

    # WHEN export_sample is calling the GenotypeAPI witch is returning a empty string

    # THEN assert CaseNotFoundError
    with pytest.raises(CaseNotFoundError):
        genotype_api.export_sample(days="")


def test_export_sample_analysis(
    genotype_api: GenotypeAPI, genotype_export_sample_analysis_output: str, caplog
):

    """Test that get_trending calls the genotype API with correct command."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a genotype api and argument days
    days = 20
    # GIVEN that the process returns some output
    genotype_api.process.stdout = genotype_export_sample_analysis_output

    # WHEN running get_trending
    genotype_api.export_sample_analysis(days=days)

    # THEN assert subprocess is running the GenotypeAPI with correct command
    call = ["config/path", "export-sample-analysis", "-d", str(days)]
    print(genotype_api)
    assert " ".join(call) in caplog.text


def test_export_sample_analysis_no_output(genotype_api: GenotypeAPI):
    """Test to get case data via the api"""

    # GIVEN a genotype api
    # GIVEN a process that does not return any output

    # WHEN export_sample is calling the GenotypeAPI witch is returning a empty string

    # THEN assert CaseNotFoundError
    with pytest.raises(CaseNotFoundError):
        genotype_api.export_sample_analysis(days=20)

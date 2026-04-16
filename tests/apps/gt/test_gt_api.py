"""
Tests for GenotypeAPI
"""

import logging

from cg.apps.gt import GenotypeAPI


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

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

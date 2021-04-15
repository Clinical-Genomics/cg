"""
    Tests for GisaidAPI
"""
import logging
import subprocess
from unittest import mock

from cg.apps.gisaid import GisaidAPI


def test_instatiate(config):

    """Test to instantiate a vogue api"""

    # GIVEN a gisaid api with a config

    # WHEN instantiating a vogue api
    gisaid_api = GisaidAPI(config)

    # THEN assert that the adapter was properly instantiated
    assert gisaid_api.gisaid_binary == config["gisaid"]["binary_path"]
    assert gisaid_api.gisaid_submitter == config["gisaid"]["submitter"]

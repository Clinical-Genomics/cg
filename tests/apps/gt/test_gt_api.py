"""
    Tests for GenotypeAPI
"""

import subprocess
import pytest

from cg.apps.gt import GenotypeAPI

from cg.exc import CaseNotFoundError


def test_instatiate(genotype_config):

    """Test to instantiate a genotype api"""

    # GIVEN a genotype api with a config

    # WHEN instantiating a genotype api
    genotype_api = GenotypeAPI(genotype_config)

    # THEN assert that the adapter was properly instantiated
    assert genotype_api.genotype_database == genotype_config['genotype']['database']
    assert genotype_api.genotype_binary == genotype_config['genotype']['binary_path']


def test_get_trending(genotypeapi, mocker):

    """Test that get_trending calls the genotype API with correct command."""

    # GIVEN a genotypeapi api and argument days
    days = '20'

    # WHEN running get_trending
    mocker.patch.object(subprocess, 'check_output')
    genotypeapi.get_trending(days=days)

    # THEN assert subprocess is running the GenotypeAPI with correct command
    call = f"gtdb --database database prepare-trending -d {days}"
    subprocess.check_output.assert_called_with(call, shell=True)


def test_get_trending_empty_inp(genotypeapi, mocker):

    """Test that get_trending calls the genotype API with correct command."""

    # GIVEN a genotypeapi api and argument days is empty string
    days = ''

    # WHEN running get_trending
    mocker.patch.object(subprocess, 'check_output')
    genotypeapi.get_trending(days=days)

    # THEN assert subprocess is running the GenotypeAPI with correct command
    subprocess.check_output.assert_called_with(f'gtdb --database database', shell=True)


def test_get_trending_no_output(genotypeapi, mocker):

    """Test to get genotype via the api"""

    # GIVEN a genotypeapi api

    # WHEN get_trending is calling the GenotypeAPI witch is returning a empty string
    mocker.patch.object(subprocess, 'check_output')
    subprocess.check_output.return_value = b''

    # THEN assert CaseNotFoundError
    with pytest.raises(CaseNotFoundError):
        genotypeapi.get_trending(days='')

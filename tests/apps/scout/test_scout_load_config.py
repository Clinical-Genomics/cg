"""Tests for the models in scout load config"""
import pytest
from pydantic import ValidationError

from cg.models.scout import scout_load_config


def test_validate_individual_display_name(sample_dict):
    """Test to validate an individual"""
    # GIVEN some sample information
    sample = sample_dict

    # WHEN validating the sample data
    ind_obj = scout_load_config.ScoutIndividual(**sample)

    # THEN assert that the display name is correct
    assert ind_obj.sample_name == sample["sample_name"]


def test_validate_mt_bam(sample_dict):
    """Test to validate an individual"""
    # GIVEN some sample information
    sample = sample_dict

    # WHEN validating the sample data
    ind_obj = scout_load_config.ScoutMipIndividual(**sample)

    # THEN assert that the mt_bam path is correct
    assert ind_obj.mt_bam == sample["mt_bam"]


def test_validate_reviewer_alignment(sample_dict):
    """Test to validate a reviewer alignment file for an individual."""
    # GIVEN some sample information
    sample = sample_dict
    # WHEN validating the sample data
    ind_obj = scout_load_config.ScoutMipIndividual(**sample)

    # THEN assert that the reviewer alignment path is set
    assert ind_obj.reviewer.alignment == sample["reviewer"]["alignment"]


def test_validate_reviewer_catalog(sample_dict):
    """Test to validate a reviewer catalogue file for an individual."""
    # GIVEN some sample information
    sample = sample_dict
    # WHEN validating the sample data
    ind_obj = scout_load_config.ScoutMipIndividual(**sample)

    # THEN assert that the reviewer alignment path is set
    assert ind_obj.reviewer.catalog == sample["reviewer"]["catalog"]


def test_instantiate_empty_mip_config():
    # GIVEN nothing

    # WHEN instantiating a empty mip load config
    config = scout_load_config.MipLoadConfig()

    # THEN assert it is possible to instantiate without any information
    assert isinstance(config, scout_load_config.ScoutLoadConfig)


def test_set_mandatory_to_none():
    """The scout load config object should validate fields as they are set

    This test will check that a value error is raised when a mandatory field is set to None
    """
    # GIVEN a load config object
    config = scout_load_config.MipLoadConfig()

    # WHEN setting a mandatory field to None
    with pytest.raises(ValidationError):
        # THEN assert a validation error was raised
        config.vcf_snv = None

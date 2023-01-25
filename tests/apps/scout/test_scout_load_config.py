"""Tests for the models in scout load config"""
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from cg.models.scout import scout_load_config
from cg.models.scout.scout_load_config import MipLoadConfig, ScoutMipIndividual
from tests.apps.scout.conftest import SCOUT_INDIVIDUAL_DICT


@pytest.mark.parametrize("key, value", list(SCOUT_INDIVIDUAL_DICT.items()))
def test_validate_scout_individual_attributes(scout_individual_dict: dict, key: str, value: Any):
    """Test to validate that all attributes of a ScoutMipIndividual are correctly set."""
    # GIVEN some sample information
    # WHEN instantiating a ScoutMipIndividual
    ind_obj: ScoutMipIndividual = scout_load_config.ScoutMipIndividual(**scout_individual_dict)

    # THEN assert that the attribute is set correctly
    assert getattr(ind_obj, key) == value


def test_validate_reviewer_alignment(scout_individual_dict: dict):
    """Test to validate a reviewer alignment file for an individual."""
    # GIVEN some sample information
    # WHEN validating the sample data
    ind_obj: ScoutMipIndividual = scout_load_config.ScoutMipIndividual(**scout_individual_dict)

    # THEN assert that the reviewer alignment path is set
    assert ind_obj.reviewer.alignment == scout_individual_dict["reviewer"]["alignment"]


def test_validate_reviewer_catalog(scout_individual_dict: dict):
    """Test to validate a reviewer catalogue file for an individual."""
    # GIVEN some sample information
    # WHEN validating the sample data
    ind_obj: ScoutMipIndividual = scout_load_config.ScoutMipIndividual(**scout_individual_dict)

    # THEN assert that the reviewer catalog path is set
    assert ind_obj.reviewer.catalog == scout_individual_dict["reviewer"]["catalog"]


def test_instantiate_empty_mip_config():
    """Tests whether a MipLoadConfig can be instantiate without arguments."""
    # GIVEN nothing

    # WHEN instantiating a empty mip load config
    config: MipLoadConfig = scout_load_config.MipLoadConfig()

    # THEN assert it is possible to instantiate without any information
    assert isinstance(config, scout_load_config.ScoutLoadConfig)


def test_set_mandatory_to_none():
    """The scout load config object should validate fields as they are set.

    This test will check that a value error is raised when a mandatory field is set to None.
    """
    # GIVEN a load config object
    config: MipLoadConfig = scout_load_config.MipLoadConfig()

    # WHEN setting a mandatory field to None
    with pytest.raises(ValidationError):
        # THEN assert a validation error was raised
        config.vcf_snv = None

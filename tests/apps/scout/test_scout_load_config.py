"""Tests for the models in scout load config"""
from typing import Any

import pytest
from pydantic.v1 import ValidationError

from cg.models.scout import scout_load_config
from cg.models.scout.scout_load_config import MipLoadConfig, ScoutMipIndividual
from tests.apps.scout.conftest import SCOUT_INDIVIDUAL


@pytest.mark.parametrize("key, value", list(SCOUT_INDIVIDUAL.items()))
def test_validate_scout_individual_attributes(scout_individual: dict, key: str, value: Any):
    """Test to validate that all attributes of a ScoutMipIndividual are correctly set."""
    # GIVEN some sample information
    # WHEN instantiating a ScoutMipIndividual
    ind_obj: ScoutMipIndividual = scout_load_config.ScoutMipIndividual(**scout_individual)

    # THEN assert that the attribute is set correctly
    assert getattr(ind_obj, key) == value


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

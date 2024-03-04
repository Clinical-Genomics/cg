"""Tests for the models in Scout load config."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from cg.models.scout import scout_load_config
from cg.models.scout.scout_load_config import MipLoadConfig, ScoutMipIndividual
from tests.apps.scout.conftest import SCOUT_INDIVIDUAL


@pytest.mark.parametrize("key, value", list(SCOUT_INDIVIDUAL.items()))
def test_validate_scout_individual_attributes(scout_individual: dict, key: str, value: Any):
    """Test that all attributes of a ScoutMipIndividual are correctly set."""

    # GIVEN some sample information

    # WHEN instantiating a ScoutMipIndividual
    ind_obj: ScoutMipIndividual = scout_load_config.ScoutMipIndividual(**scout_individual)

    # THEN assert that the attribute is set correctly
    assert getattr(ind_obj, key) == value


def test_instantiate_empty_mip_config(delivery_report_html: Path):
    """Tests whether a MipLoadConfig can be instantiated only with mandatory arguments."""

    # GIVEN a delivery report file

    # WHEN instantiating an empty MIP load config
    config: MipLoadConfig = scout_load_config.MipLoadConfig(
        delivery_report=delivery_report_html.as_posix()
    )

    # THEN assert it is possible to instantiate without any not mandatory information
    assert isinstance(config, scout_load_config.ScoutLoadConfig)


def test_set_mandatory_to_none(delivery_report_html: Path):
    """Test that a value error is raised when a mandatory field is set to None."""

    # GIVEN a load config object
    config: MipLoadConfig = scout_load_config.MipLoadConfig(
        delivery_report=delivery_report_html.as_posix()
    )

    # WHEN setting a mandatory field to None
    with pytest.raises(ValidationError):
        # THEN a validation error should be raised
        config.vcf_snv = None

"""Tests for the models in scout load config"""

from cg.apps.scout import scout_load_config


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
    ind_obj = scout_load_config.ScoutIndividual(**sample)

    # THEN assert that the mt_bam path is correct
    assert ind_obj.mt_bam == sample["mt_bam"]

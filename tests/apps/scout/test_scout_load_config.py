"""Tests for the models in scout load config"""

from cg.apps.scout import scout_load_config


def test_validate_individual_display_name():
    """Test to validate an individual"""
    # GIVEN some sample information
    sample = {
        "analysis_type": "wgs",
        "bam_path": "/path/to/sample.bam",
        "capture_kit": None,
        "father": "0",
        "mother": "0",
        "sample_id": "sample_id",
        "sample_name": "sample_name",
        "sex": "male",
        "tissue_type": "unknown",
        "phenotype": "affected",
    }

    # WHEN validating the sample data
    ind_obj = scout_load_config.ScoutIndividual(**sample)

    # THEN assert that the display name is correct
    assert ind_obj.sample_name == sample["sample_name"]

from cg.apps.demultiplex.sample_sheet.sample_models import IlluminaSampleIndexSetting
from cg.apps.demultiplex.sample_sheet.validators import is_valid_sample_internal_id


def test_is_valid_sample_internal_id(
    novaseq6000_flow_cell_sample_1: IlluminaSampleIndexSetting,
    novaseq6000_flow_cell_sample_2: IlluminaSampleIndexSetting,
):
    """Test that validating two different samples finishes successfully."""
    # GIVEN two different NovaSeq samples with valid internal IDs

    # WHEN validating the sample internal ids
    for sample in [novaseq6000_flow_cell_sample_1, novaseq6000_flow_cell_sample_2]:
        # THEN no error is raised
        assert is_valid_sample_internal_id(sample_internal_id=sample.sample_id)


def test_is_valid_sample_internal_id_invalid_sample_internal_ids(
    novaseq6000_flow_cell_sample_1: IlluminaSampleIndexSetting,
    novaseq6000_flow_cell_sample_2: IlluminaSampleIndexSetting,
):
    """Test that validating two different samples finishes successfully."""
    # GIVEN two different NovaSeq samples with valid internal IDs

    # WHEN setting the sample internal ids to invalid values
    novaseq6000_flow_cell_sample_1.sample_id = "invalid_sample_id"
    novaseq6000_flow_cell_sample_2.sample_id = "invalid_sample_id"

    # WHEN validating the sample internal ids
    # THEN no error is raised
    for sample in [novaseq6000_flow_cell_sample_1, novaseq6000_flow_cell_sample_2]:
        assert not is_valid_sample_internal_id(sample_internal_id=sample.sample_id)

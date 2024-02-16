from pathlib import Path

from cg.apps.demultiplex.sample_sheet.sample_sheet_models import SampleSheet
from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import SampleSheetValidator
from cg.apps.demultiplex.sample_sheet.validators import is_valid_sample_internal_id


def test_get_sample_internal_ids_from_sample_sheet(
    novaseq_6000_post_1_5_kits_correct_sample_sheet_path: Path,
):
    """Test that getting sample internal ids from a sample sheet returns a unique list of strings."""

    # GIVEN a sample hseet validator
    validator = SampleSheetValidator()

    # GIVEN a sample sheet with only valid samples
    sample_sheet: SampleSheet = validator.get_sample_sheet_object_from_file(
        novaseq_6000_post_1_5_kits_correct_sample_sheet_path
    )

    # WHEN getting the valid sample internal ids
    sample_internal_ids: list[str] = sample_sheet.get_sample_ids()

    # THEN the returned value is a list
    assert isinstance(sample_internal_ids, list)
    # THEN the list contains strings
    assert isinstance(sample_internal_ids[0], str)
    # THEN the sample internal ids are unique
    assert len(sample_internal_ids) == len(set(sample_internal_ids))
    # THEN the sample internal ids are the expected ones
    for sample_internal_id in sample_internal_ids:
        assert is_valid_sample_internal_id(sample_internal_id=sample_internal_id) is True

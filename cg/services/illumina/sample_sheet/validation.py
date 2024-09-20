import logging

from cg.services.illumina.sample_sheet.exc import SampleSheetValidationError
from cg.services.illumina.sample_sheet.models import IlluminaSampleIndexSetting

LOG = logging.getLogger(__name__)


def field_list_elements_validation(attribute: str, value: list[str], name: str) -> list[str]:
    """Validate that the list has two elements and the first element is the expected name."""
    if len(value) != 2:
        raise ValueError(f"{attribute} must have two entries.")
    elif value[0] != name:
        raise ValueError(f"The first entry of {attribute} must be '{name}'.")
    return value


def field_default_value_validation(
    attribute: str, value: list[str], default: list[str]
) -> list[str]:
    """Validate that the value is the default value."""
    if value != default:
        raise ValueError(f"{attribute} must be set to the default value: {default}")
    return value


def validate_samples_are_unique(samples: list[IlluminaSampleIndexSetting]) -> None:
    """Validate that each sample only exists once."""
    sample_ids: set = set()
    for sample in samples:
        sample_id: str = sample.sample_id.split("_")[0]
        if sample_id in sample_ids:
            message: str = f"Sample {sample.sample_id} exists multiple times in sample sheet"
            LOG.error(message)
            raise SampleSheetValidationError(message)
        sample_ids.add(sample_id)


def validate_samples_unique_per_lane(samples: list[IlluminaSampleIndexSetting]) -> None:
    """Validate that each sample only exists once per lane in a sample sheet."""
    sample_by_lane: dict[int, list[IlluminaSampleIndexSetting]] = get_samples_by_lane(samples)
    for lane, lane_samples in sample_by_lane.items():
        LOG.debug(f"Validate that samples are unique in lane: {lane}")
        validate_samples_are_unique(samples=lane_samples)

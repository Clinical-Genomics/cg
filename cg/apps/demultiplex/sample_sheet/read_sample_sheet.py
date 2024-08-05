import logging

from pydantic import TypeAdapter

from cg.apps.demultiplex.sample_sheet.sample_models import IlluminaSampleIndexSetting
from cg.constants.demultiplexing import SampleSheetBcl2FastqSections, SampleSheetBCLConvertSections
from cg.exc import SampleSheetContentError, SampleSheetFormatError

LOG = logging.getLogger(__name__)


def validate_samples_are_unique(samples: list[IlluminaSampleIndexSetting]) -> None:
    """Validate that each sample only exists once."""
    sample_ids: set = set()
    for sample in samples:
        sample_id: str = sample.sample_id.split("_")[0]
        if sample_id in sample_ids:
            message: str = f"Sample {sample.sample_id} exists multiple times in sample sheet"
            LOG.error(message)
            raise SampleSheetContentError(message)
        sample_ids.add(sample_id)


def validate_samples_unique_per_lane(samples: list[IlluminaSampleIndexSetting]) -> None:
    """Validate that each sample only exists once per lane in a sample sheet."""
    sample_by_lane: dict[int, list[IlluminaSampleIndexSetting]] = get_samples_by_lane(samples)
    for lane, lane_samples in sample_by_lane.items():
        LOG.debug(f"Validate that samples are unique in lane: {lane}")
        validate_samples_are_unique(samples=lane_samples)


def get_raw_samples_from_content(sample_sheet_content: list[list[str]]) -> list[dict[str, str]]:
    """Return the samples in a sample sheet as a list of dictionaries."""
    header: list[str] = []
    raw_samples: list[dict[str, str]] = []

    for line in sample_sheet_content:
        # Skip lines that are too short to contain samples
        if len(line) <= 4:
            continue
        if line[0] in [
            SampleSheetBcl2FastqSections.Data.FLOW_CELL_ID.value,
            SampleSheetBCLConvertSections.Data.LANE.value,
        ]:
            header = line
            continue
        if not header:
            continue
        raw_samples.append(dict(zip(header, line)))
    if not header:
        message = "Could not find header in sample sheet"
        LOG.warning(message)
        raise SampleSheetFormatError(message)
    if not raw_samples:
        message = "Could not find any samples in sample sheet"
        LOG.warning(message)
        raise SampleSheetFormatError(message)
    return raw_samples


def get_samples_by_lane(
    samples: list[IlluminaSampleIndexSetting],
) -> dict[int, list[IlluminaSampleIndexSetting]]:
    """Group and return samples by lane."""
    LOG.debug("Order samples by lane")
    sample_by_lane: dict[int, list[IlluminaSampleIndexSetting]] = {}
    for sample in samples:
        if sample.lane not in sample_by_lane:
            sample_by_lane[sample.lane] = []
        sample_by_lane[sample.lane].append(sample)
    return sample_by_lane


def get_samples_from_content(
    sample_sheet_content: list[list[str]],
) -> list[IlluminaSampleIndexSetting]:
    """
    Return the samples in a sample sheet as a list of IlluminaIndexSettings objects.
    Raises:
        ValidationError: if the samples do not have the correct attributes based on their model.
    """
    raw_samples: list[dict[str, str]] = get_raw_samples_from_content(
        sample_sheet_content=sample_sheet_content
    )
    adapter = TypeAdapter(list[IlluminaSampleIndexSetting])
    return adapter.validate_python(raw_samples)

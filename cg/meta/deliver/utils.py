from copy import deepcopy
import logging
import os
from pathlib import Path
from cg.constants import delivery as constants
from cg.constants.constants import Pipeline
from cg.store.models import Case, Sample
from housekeeper.store.models import File, Version

LOG = logging.getLogger(__name__)


def get_delivery_scope(delivery_arguments: set[str]) -> tuple[bool, bool]:
    """Returns the scope of the delivery, ie whether sample and/or case files were delivered."""
    case_delivery: bool = False
    sample_delivery: bool = False
    for delivery in delivery_arguments:
        if (
            constants.PIPELINE_ANALYSIS_TAG_MAP[delivery]["sample_tags"]
            and delivery in constants.ONLY_ONE_CASE_PER_TICKET
        ):
            sample_delivery = True
        if constants.PIPELINE_ANALYSIS_TAG_MAP[delivery]["case_tags"]:
            case_delivery = True
    return sample_delivery, case_delivery


def get_delivery_dir_path(
    base_path: Path,
    customer_id: str,
    ticket: str,
    case_name: str = None,
    sample_name: str = None,
) -> Path:
    """Get a path for delivering files.

    Note that case name and sample name needs to be the identifiers sent from customer.
    """
    delivery_path = Path(base_path, customer_id, constants.INBOX_NAME, ticket)
    if case_name:
        delivery_path = delivery_path / case_name
    if sample_name:
        delivery_path = delivery_path / sample_name
    return delivery_path


def get_case_tags_for_pipeline(pipeline: Pipeline) -> list[set[str]]:
    return constants.PIPELINE_ANALYSIS_TAG_MAP[pipeline]["case_tags"]


def get_sample_tags_for_pipeline(pipeline: Pipeline) -> list[set[str]]:
    return constants.PIPELINE_ANALYSIS_TAG_MAP[pipeline]["sample_tags"]


def get_delivery_case_name(case: Case, pipeline: str) -> str | None:
    return None if pipeline in constants.ONLY_ONE_CASE_PER_TICKET else case.name


def get_out_path(out_dir: Path, file: Path, case: Case) -> Path:
    out_file_name: str = _get_case_out_file_name(file=file, case=case)
    return Path(out_dir, out_file_name)


def _get_case_out_file_name(file: Path, case: Case) -> str:
    return file.name.replace(case.internal_id, case.name)


def get_sample_out_file_name(file: Path, sample: Sample) -> str:
    return file.name.replace(sample.internal_id, sample.name)


def include_file_case(file: File, sample_ids: set[str], pipeline: str) -> bool:
    """Check if file should be included in case bundle.

    At least one tag should match between file and tags.
    Do not include files with sample tags.
    """
    file_tags = {tag.name for tag in file.tags}
    case_tags = get_case_tags_for_pipeline(pipeline)
    all_case_tags: set[str] = {tag for tags in case_tags for tag in tags}
    if all_case_tags.isdisjoint(file_tags):
        LOG.debug("No tags are matching")
        return False

    LOG.debug(f"Found file tags {', '.join(file_tags)}")

    # Check if any of the sample tags exist
    if sample_ids.intersection(file_tags):
        LOG.debug(f"Found sample tag, skipping {file.path}")
        return False

    # Check if any of the file tags matches the case tags
    tags: set[str]
    for tags in case_tags:
        LOG.debug(f"check if {tags} is a subset of {file_tags}")
        if tags.issubset(file_tags):
            return True
    LOG.debug(f"Could not find any tags matching file {file.path} with tags {file_tags}")

    return False


def include_file_sample(file: File, sample_id: str, pipeline: str) -> bool:
    """Check if file should be included in sample bundle.

    At least one tag should match between file and tags.
    Only include files with sample tag.

    For fastq delivery we know that we want to deliver all files of bundle.
    """
    file_tags = {tag.name for tag in file.tags}
    tags: set[str]
    # Check if any of the file tags matches the sample tags
    sample_tags = get_sample_tags_for_pipeline(pipeline)
    for tags in sample_tags:
        working_copy = deepcopy(tags)
        if pipeline != "fastq":
            working_copy.add(sample_id)
        if working_copy.issubset(file_tags):
            return True
    return False


def create_link(source: Path, destination: Path, dry_run: bool = False) -> bool:
    if dry_run:
        LOG.info(f"Would hard link file {source} to {destination}")
        return True
    try:
        os.link(source, destination)
        LOG.info(f"Hard link file {source} to {destination}")
        return True
    except FileExistsError:
        LOG.info(f"Path {destination} exists, skipping")
        return False

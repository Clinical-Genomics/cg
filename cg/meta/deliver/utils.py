import logging
import os
from pathlib import Path
from cg.constants import delivery as constants
from cg.constants.constants import Workflow
from cg.store.models import Case, Sample
from housekeeper.store.models import File

LOG = logging.getLogger(__name__)


def get_delivery_scope(workflows: list[str]) -> tuple[bool, bool]:
    """Returns the scope of the delivery, ie whether sample and/or case files were delivered."""
    case_delivery: bool = False
    sample_delivery: bool = False
    for workflow in workflows:
        if is_sample_delivery(workflow):
            sample_delivery = True
        if is_case_delivery(workflow):
            case_delivery = True
    return sample_delivery, case_delivery


def is_sample_delivery(workflow: str) -> bool:
    return get_sample_tags_for_workflow(workflow) and workflow_has_one_case_per_ticket(workflow)


def is_case_delivery(workflow: str) -> bool:
    return get_case_tags_for_workflow(workflow)


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
        delivery_path = Path(delivery_path, case_name)
    if sample_name:
        delivery_path = Path(delivery_path, sample_name)
    return delivery_path


def workflow_has_one_case_per_ticket(workflow: Workflow) -> bool:
    return workflow in constants.ONLY_ONE_CASE_PER_TICKET


def get_case_tags_for_workflow(workflow: Workflow) -> list[set[str]]:
    return constants.PIPELINE_ANALYSIS_TAG_MAP[workflow]["case_tags"]


def get_sample_tags_for_workflow(workflow: Workflow) -> list[set[str]]:
    return constants.PIPELINE_ANALYSIS_TAG_MAP[workflow]["sample_tags"]


def get_delivery_case_name(case: Case, workflow: str) -> str | None:
    return None if workflow in constants.ONLY_ONE_CASE_PER_TICKET else case.name


def get_out_path(out_dir: Path, file: Path, case: Case) -> Path:
    out_file_name: str = _get_case_out_file_name(file=file, case=case)
    return Path(out_dir, out_file_name)


def _get_case_out_file_name(file: Path, case: Case) -> str:
    return file.name.replace(case.internal_id, case.name)


def get_sample_out_file_name(file: Path, sample: Sample) -> str:
    return file.name.replace(sample.internal_id, sample.name)


def should_include_file_case(file: File, sample_ids: set[str], workflow: str) -> bool:
    """Check if file should be included in case bundle.

    At least one tag should match between file and tags.
    Do not include files with sample tags.
    """
    tags_on_file = {tag.name for tag in file.tags}
    case_tags = get_case_tags_for_workflow(workflow)

    if sample_ids.intersection(tags_on_file):
        return False

    return any(tags.issubset(tags_on_file) for tags in case_tags)


def should_include_file_sample(file: File, workflow: str) -> bool:
    """Check if file should be included in sample bundle.

    At least one tag should match between file and the sample tags.
    """
    file_tags = {tag.name for tag in file.tags}
    sample_tags = get_sample_tags_for_workflow(workflow)
    return any(tags.issubset(file_tags) for tags in sample_tags)


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


def get_bundle_name(case: Case, sample: Sample, workflow: str) -> str:
    return sample.internal_id if workflow == Workflow.FASTQ else case.internal_id

from pathlib import Path
from cg.constants import delivery as constants


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


def create_delivery_dir_path(
    base_path: Path,
    customer_id: str,
    ticket: str,
    case_name: str = None,
    sample_name: str = None,
) -> Path:
    """Create a path for delivering files.

    Note that case name and sample name needs to be the identifiers sent from customer.
    """
    delivery_path = Path(base_path, customer_id, constants.INBOX_NAME, ticket)
    if case_name:
        delivery_path = delivery_path / case_name
    if sample_name:
        delivery_path = delivery_path / sample_name
    return delivery_path

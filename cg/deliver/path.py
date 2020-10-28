"""Code that works with paths in the delivery context"""

import logging
from pathlib import Path

LOG = logging.getLogger(__name__)


def create_delivery_dir(
    project_path: Path, ticket_id: str, customer_id: str, case_id: str, sample_name: str = None
) -> None:
    """Create a path for delivering files"""
    delivery_path = project_path / customer_id / "inbox" / ticket_id / case_id
    if sample_name:
        delivery_path = delivery_path / sample_name
    LOG.debug("Creating project path %s", delivery_path)
    delivery_path.mkdir(parents=True, exist_ok=True)


def generate_case_delivery_path(case, case_obj, file_obj, out_dir):
    return Path(f"{out_dir / Path(file_obj.path).name.replace(case, case_obj.name)}")


def generate_sample_delivery_path(file_obj, out_dir, sample_obj):
    return Path(
        f"{out_dir / Path(file_obj.path).name.replace(sample_obj.internal_id, sample_obj.name)}"
    )

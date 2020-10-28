"""Code for delivering files with CG"""

import logging

from typing import Iterable, List
from datetime import datetime
from pathlib import Path

from cg.store.models import Family, FamilySample
from cg.store import Store

from cg.meta.deliver import DeliverAPI

from .path import create_inbox_dir

LOG = logging.getLogger(__name__)

# This could be replaced with something more dynamic if necessary
PROJECT_BASE_PATH = Path("/home/proj/production/customers")


def deliver_to_inbox(
    store: Store,
    deliver_api: DeliverAPI,
    project_base_path: Path = None,
    ticket_id: int = None,
    case_id: str = None,
):
    """Deliver files to the inbox of a customer"""

    project_base_path = project_base_path or PROJECT_BASE_PATH
    LOG.debug("Use base path for project out dir %s", project_base_path)
    # if ticket_id:
    #     # TODO fetch cases based on ticket id here
    #     case_objs: List[Family] = []
    # else:
    #     case_obj: Family = store.family(case_id)
    #     if case_obj is None:
    #         LOG.warning("Could not find case %s", case_id)
    #         return None
    #     case_objs: List[Family] = [case_obj]
    case_obj: Family = store.family(case_id)
    customer_id: str = case_obj.customer.internal_id

    # Fetch the samples linked to case
    link_objs: List[FamilySample] = store.family_samples(case_id)
    if not link_objs:
        LOG.warning("Could not find any samples linked to case %s", case_id)
        return None

    ticket_id: int = link_objs[0].sample.ticket_number
    create_inbox_dir(ticket_id=str(ticket_id), customer_id=customer_id, case_id=case_id)

    files: List[Path] = deliver_api.get_post_analysis_case_files(case=case_id)
    if not files:
        LOG.warning("No case files found")

    out_dir = Path(inbox_path.format(case=case_obj.name, customer=case_obj.customer.internal_id))
    LOG.info("Creating directory %s", out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for file_obj in files:

        out_path = _generate_case_delivery_path(case, case_obj, file_obj, out_dir)
        in_path = Path(file_obj.full_path)

        if not out_path.exists():
            os.link(in_path, out_path)
            LOG.info("linked file: %s -> %s", in_path, out_path)
        else:
            LOG.info("Target file exists: %s", out_path)

    if not link_obj:
        LOG.warning("No sample files found.")

    for case_sample in link_obj:
        sample_obj = case_sample.sample
        files = context.obj["deliver_api"].get_post_analysis_sample_files(
            case=case, sample=sample_obj.internal_id, version=version, tag=tag
        )

        if not files:
            LOG.warning("No sample files found for '%s'.", sample_obj.internal_id)

        for file_obj in files:
            out_dir = Path(
                inbox_path.format(case=case_obj.name, customer=case_obj.customer.internal_id)
            )
            out_dir = out_dir.joinpath(sample_obj.name)
            out_dir.mkdir(parents=True, exist_ok=True)

            out_path = _generate_sample_delivery_path(file_obj, out_dir, sample_obj)
            in_path = Path(file_obj.full_path)

            if not out_path.exists():
                os.link(in_path, out_path)
                LOG.info("linked file: %s -> %s", in_path, out_path)
            else:
                LOG.info("Target file exists: %s", out_path)

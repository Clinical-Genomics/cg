"""Helper functions for compress cli"""
import logging
from typing import List

from cg.exc import CaseNotFoundError
from cg.meta.compress import CompressAPI
from cg.store import Store, models

LOG = logging.getLogger(__name__)


def get_cases(store: Store, case_id: str = None) -> List[models.Family]:
    """Fetch cases from store

    I case_id return one case (if existing) otherwise return all
    """
    if case_id:
        case_obj = store.family(case_id)
        if not case_obj:
            LOG.warning("Could not find case %s", case_id)
            raise CaseNotFoundError("")
        return [case_obj]
    return store.families()


def update_compress_api(
    compress_api: CompressAPI, dry_run: bool, ntasks: int = None, mem: int = None
) -> None:
    """Update parameters in compress api"""

    LOG.info("Update compress api %s", ntasks)
    compress_api.set_dry_run(dry_run)
    if ntasks:
        LOG.info("Set ntasks to %s", ntasks)
        compress_api.ntasks = ntasks
    if mem:
        LOG.info("Set mem to %s", ntasks)
        compress_api.mem = mem

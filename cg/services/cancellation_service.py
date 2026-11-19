import logging

from cg.exc import CaseNotFoundError
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


def cases(case_ids: set[str], comment: str, status_db: Store) -> None:
    """
    Cancel the given cases in StatusDB.

    For each case:
        - mark it as cancelled,
        - add the comment
        - set the should_deliver_sample to False for the connected CaseSamples.

    Changes are not committed; the caller is responsible for committing or rolling back.

    Raises:
        CaseNotFoundError: If any of the cases do not exist. Nothing is modified then.
    """

    cases_to_cancel: list[Case] = _get_cases_strict(case_ids=case_ids, status_db=status_db)
    for case in cases_to_cancel:
        _cancel_case(case=case, comment=comment, status_db=status_db)

    # TODO: close orders if only cancelled cases? Might be too much work
    # TODO: close ticket if only cancelled cases? Might be too much work


def _get_cases_strict(case_ids: set[str], status_db: Store) -> list[Case]:
    """Gets all the cases only if all cases exists, raises `CaseNotFoundError` if there is any missing case"""
    found_cases: list[Case] = status_db.get_cases_by_internal_ids(list(case_ids))
    found_ids: set[str] = {case.internal_id for case in found_cases}

    missing_ids: set[str] = case_ids - found_ids
    if missing_ids:
        raise CaseNotFoundError(f"Cases not found: {', '.join(sorted(missing_ids))}")

    return found_cases


def _cancel_case(case: Case, comment: str, status_db: Store) -> None:
    status_db.update_case_is_cancelled(case=case, state=True)
    status_db.update_case_comment(case=case, comment=comment)
    LOG.debug(f"Case {case.internal_id} cancelled with {comment=}")
    for link in case.links:
        status_db.update_should_deliver_sample(link=link, state=False)
        LOG.debug(f"Case {case.internal_id} will not deliver sample {link.sample.internal_id}")

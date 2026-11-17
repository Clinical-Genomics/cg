from cg.exc import CaseNotFoundError
from cg.store.models import Case
from cg.store.store import Store


def cases(case_ids: list[str], comment: str, status_db: Store) -> None:
    cases_to_cancel: list[Case] = _get_cases_strict(case_ids=case_ids, status_db=status_db)
    for case in cases_to_cancel:
        _cancel_cases(case=case, comment=comment, status_db=status_db)


def _get_cases_strict(case_ids: list[str], status_db: Store) -> list[Case]:
    found_cases: list[Case] = status_db.get_cases_by_internal_ids(case_ids)

    found_ids: set[str] = {case.internal_id for case in found_cases}
    missing_ids: list[str] = []
    for case_id in case_ids:
        if case_id not in found_ids:
            missing_ids.append(case_id)

    if missing_ids:
        raise CaseNotFoundError(f"Cases not found: {', '.join(missing_ids)}")

    return found_cases


def _cancel_cases(case: Case, comment: str, status_db: Store):
    status_db.update_case_comment(case_id=case.id, comment=comment)
    status_db.update_case_is_canceled(case_id=case.id, comment=comment)
    # TODO: The CaseSample should deliver this sample. Should not deliver the sample
    # TODO: get all the CaseSample and mark as should not deliver

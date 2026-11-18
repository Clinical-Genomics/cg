from unittest.mock import call, create_autospec

import pytest

from cg.exc import CaseNotFoundError
from cg.services import cancellation_service
from cg.store.models import Case, CaseSample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_cases_success():
    # GIVEN a store
    status_db: TypedMock[Store] = create_typed_mock(Store)

    # GIVEN case ids that exist in statusDB, each case with linked samples
    cases_ids = ["amazingdog", "shittycow"]
    comment = "a comment"

    dog_link: CaseSample = create_autospec(CaseSample, instance=True)
    cow_link_1: CaseSample = create_autospec(CaseSample, instance=True)
    cow_link_2: CaseSample = create_autospec(CaseSample, instance=True)

    dog_case: Case = create_autospec(
        Case, instance=True, internal_id=cases_ids[0], links=[dog_link]
    )
    cow_case: Case = create_autospec(
        Case, instance=True, internal_id=cases_ids[1], links=[cow_link_1, cow_link_2]
    )

    status_db.as_mock.get_cases_by_internal_ids.return_value = [dog_case, cow_case]

    # WHEN cancelling a list of case_ids
    cancellation_service.cases(case_ids=cases_ids, comment=comment, status_db=status_db.as_type)

    # THEN each case is marked as cancelled
    status_db.as_mock.update_case_is_cancelled.assert_has_calls(
        [call(case=dog_case, state=True), call(case=cow_case, state=True)]
    )
    assert status_db.as_mock.update_case_is_cancelled.call_count == 2

    # THEN the comment is added to each case
    status_db.as_mock.update_case_comment.assert_has_calls(
        [call(case=dog_case, comment=comment), call(case=cow_case, comment=comment)]
    )
    assert status_db.as_mock.update_case_comment.call_count == 2

    # THEN no sample in the cases should be delivered
    status_db.as_mock.update_should_deliver_sample.assert_has_calls(
        [
            call(link=dog_link, state=False),
            call(link=cow_link_1, state=False),
            call(link=cow_link_2, state=False),
        ]
    )
    assert status_db.as_mock.update_should_deliver_sample.call_count == 3


def test_cases_missing_case_raises():
    # GIVEN a store
    status_db: TypedMock[Store] = create_typed_mock(Store)

    # GIVEN case ids where one does not exist in statusDB
    cases_ids = ["amazingdog", "shittycow"]
    dog_case: Case = create_autospec(Case, instance=True, internal_id=cases_ids[0], links=[])
    status_db.as_mock.get_cases_by_internal_ids.return_value = [dog_case]

    # WHEN cancelling the cases
    # THEN a CaseNotFoundError is raised naming the missing case
    with pytest.raises(CaseNotFoundError, match="shittycow"):
        cancellation_service.cases(
            case_ids=cases_ids, comment="a comment", status_db=status_db.as_type
        )

    # THEN no case is modified
    status_db.as_mock.update_case_is_cancelled.assert_not_called()
    status_db.as_mock.update_case_comment.assert_not_called()
    status_db.as_mock.update_should_deliver_sample.assert_not_called()

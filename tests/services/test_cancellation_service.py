from cg.services import cancellation_service
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_cases_success():
    # GIVEN case ids that exist in statusDB
    cases_ids = ["amazingdog", "shittycow"]

    comment = ""

    # GIVEN a store
    status_db: TypedMock[Store] = create_typed_mock(Store)

    # WHEN cancelling a list of case_ids
    cancellation_service.cases(case_ids=cases_ids, comment=comment, status_db=status_db.as_type)

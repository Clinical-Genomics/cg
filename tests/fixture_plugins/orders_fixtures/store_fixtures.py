import pytest

from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def store_with_rml_applications(store: Store, helpers: StoreHelpers) -> Store:
    app_tags: list[str] = ["RMLP15R100", "RMLP15R200", "RMLP15R400", "RMLP15R500"]
    for tag in app_tags:
        helpers.ensure_application_version(
            store=store,
            application_tag=tag,
            prep_category=SeqLibraryPrepCategory.READY_MADE_LIBRARY,
        )
    helpers.ensure_customer(store=store, customer_id="cust000")
    return store

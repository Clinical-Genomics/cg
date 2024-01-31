from datetime import datetime

from cg.store.models import Application, ApplicationVersion
from cg.store.store import Store


def test_add_application_version(
    store_with_an_application_with_and_without_attributes: Store,
    timestamp: datetime,
    prices: dict[str, int],
    version: int = 1,
):
    """Test that the functions returns an application version."""
    # GIVEN a store with applications but without application versions
    applications: list[Application] = (
        store_with_an_application_with_and_without_attributes.get_applications()
    )
    store_with_an_application_with_and_without_attributes._get_query(table=ApplicationVersion).all()
    assert len(applications) > 0
    assert (
        len(
            store_with_an_application_with_and_without_attributes._get_query(
                table=ApplicationVersion
            ).all()
        )
        == 0
    )

    # WHEN adding a new application version
    version: ApplicationVersion = (
        store_with_an_application_with_and_without_attributes.add_application_version(
            application=applications[0], version=version, valid_from=timestamp, prices=prices
        )
    )
    store_with_an_application_with_and_without_attributes.session.add(version)

    # THEN the store has one application version
    assert (
        len(
            store_with_an_application_with_and_without_attributes._get_query(
                table=ApplicationVersion
            ).all()
        )
        == 1
    )

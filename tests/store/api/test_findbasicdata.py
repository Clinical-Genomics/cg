from typing import Optional, List

from sqlalchemy.orm import Query

from cg.store import Store
from cg.store.models import Bed, BedVersion, Collaboration, Customer, User


def test_get_bed_query(base_store: Store):
    """Test function to return the bed query."""

    # GIVEN a store with bed records

    # WHEN getting the query for the beds
    bed_query: Query = base_store._get_bed_query()

    # THEN a query should be returned
    assert isinstance(bed_query, Query)


def test_get_user_query(store_with_users: Store):
    """Test function to return the user query."""

    # WHEN getting the query for the users
    user_query: Query = store_with_users._get_user_query()

    # THEN a query should be returned
    assert isinstance(user_query, Query)


def test_get_beds(base_store: Store):
    """Test returning bed records query."""

    # GIVEN a store with beds

    # WHEN fetching beds
    beds: Query = base_store.get_beds()

    # THEN beds should have be returned
    assert beds


def test_get_active_beds(base_store: Store):
    """Test returning not archived bed records from the database."""

    # GIVEN a store with beds

    # WHEN fetching beds
    beds: Query = base_store.get_active_beds()

    # THEN beds should have be returned
    assert beds

    # THEN the bed records should not be archived
    for bed in beds:
        assert bed.is_archived is False


def test_get_active_beds_when_archived(base_store: Store):
    """Test returning not archived bed records from the database when archived."""

    # GIVEN a store with beds
    beds: Query = base_store.get_active_beds()
    for bed in beds:
        bed.is_archived = True
        base_store.add_commit(bed)

    # WHEN fetching beds
    active_beds: Query = base_store.get_active_beds()

    # THEN return no beds
    assert not list(active_beds)


def test_get_bed_by_name(base_store: Store, bed_name: str):
    """Test returning a bed record by name from the database."""

    # GIVEN a store with beds

    # WHEN fetching beds
    bed: Optional[Bed] = base_store.get_bed_by_name(bed_name=bed_name)

    # THEN return a bed
    assert bed

    # THEN return a bed with the supplied bed name
    assert bed.name == bed_name


def test_get_bed_by_name_when_no_match(base_store: Store):
    """Test returning a bed record by name from the database when no match."""

    # GIVEN a store with beds

    # WHEN fetching beds
    bed: Optional[Bed] = base_store.get_bed_by_name(bed_name="does_not_exist")

    # THEN do not return a bed
    assert not bed


def test_get_latest_bed_version(base_store: Store, bed_name: str):
    """Test returning a bed version by bed name from the database."""

    # GIVEN a store with beds

    # WHEN fetching beds
    bed_version: BedVersion = base_store.get_latest_bed_version(bed_name=bed_name)

    # THEN return a bed version with the supplied bed name
    assert bed_version.version == 1


def test_get_application_query(base_store: Store):
    """Test function to return the application query."""

    # GIVEN a store with application records

    # WHEN getting the query for the flow cells
    application_query: Query = base_store._get_application_query()

    # THEN a query should be returned
    assert isinstance(application_query, Query)


def test_get_bed_version_query(base_store: Store):
    """Test function to return the bed version query."""

    # GIVEN a store with bed versions records

    # WHEN getting the query for the bed versions
    bed_version_query: Query = base_store._get_bed_version_query()

    # THEN a query should be returned
    assert isinstance(bed_version_query, Query)


def test_get_bed_version_by_short_name(base_store: Store, bed_version_short_name: str):
    """Test function to return the bed version by short name."""

    # GIVEN a store with bed versions records

    # WHEN getting the query for the bed versions
    bed_version: BedVersion = base_store.get_bed_version_by_short_name(
        bed_version_short_name=bed_version_short_name
    )

    # THEN return a bed version with the supplied bed version short name
    assert bed_version.shortname == bed_version_short_name


def test_get_customer_query(base_store: Store):
    """Test function to return the customer query."""

    # GIVEN a store with customer records

    # WHEN getting the query for the customers
    customer_query: Query = base_store._get_customer_query()

    # THEN a query should be returned
    assert isinstance(customer_query, Query)


def test_get_customer_by_customer_id(base_store: Store, customer_id: str):
    """Test function to return the customer by customer id."""

    # GIVEN a store with customer records

    # WHEN getting the query for the customer
    customer: Customer = base_store.get_customer_by_customer_id(customer_id=customer_id)

    # THEN return a customer with the supplied customer internal id
    assert customer.internal_id == customer_id


def test_get_customers(base_store: Store, customer_id: str):
    """Test function to return customers."""

    # GIVEN a store with customer records

    # WHEN getting the customers
    customers: List[Customer] = base_store.get_customers()

    # THEN return customers
    assert customers

    # THEN return a customer with the database customer internal id
    assert customers[0].internal_id == customer_id


def test_get_collaboration_by_internal_id(base_store: Store, collaboration_id: str):
    """Test function to return the collaborations by internal_id."""

    # GIVEN a store with collaborations

    # WHEN getting the query for the collaborations
    collaboration: Collaboration = base_store.get_collaboration_by_internal_id(
        internal_id=collaboration_id
    )

    # THEN return a collaboration with the give collaboration internal_id
    assert collaboration.internal_id == collaboration_id


def test_get_user_by_email_returns_correct_user(store_with_users: Store):
    """Test fetching a user by email."""

    # GIVEN a store with multiple users
    num_users: int = store_with_users._get_user_query().count()
    assert num_users > 0

    # Select a random user from the store
    user: User = store_with_users._get_user_query().first()
    assert user is not None

    # WHEN fetching the user by email
    filtered_user: User = store_with_users.get_user_by_email(email=user.email)

    # THEN a user should be returned
    assert isinstance(filtered_user, User)

    # THEN the email should match
    assert filtered_user.email == user.email


def test_get_user_by_email_returns_none_for_nonexisting_email(
    store_with_users: Store, non_existent_email: str
):
    """Test getting user by email when the email does not exist."""

    # GIVEN a non-existing email

    # WHEN retrieving the user by email
    filtered_user: User = store_with_users.get_user_by_email(email=non_existent_email)

    # THEN no user should be returned
    assert filtered_user is None


def test_get_user_when_email_is_none_returns_none(store_with_users: Store):
    """Test getting user by email when the email is None."""

    # WHEN retrieving filtering by email None
    filtered_user: User = store_with_users.get_user_by_email(email=None)

    # THEN no user should be returned
    assert filtered_user is None

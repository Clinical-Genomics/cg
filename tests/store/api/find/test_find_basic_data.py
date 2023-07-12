from typing import Optional, List
from sqlalchemy.orm import Query
from cg.constants.constants import MicrosaltAppTags
from cg.store import Store
from cg.store.models import (
    Application,
    Bed,
    BedVersion,
    Customer,
    Collaboration,
    Organism,
    User,
)


def test_get_bed_by_entry_id(base_store: Store, entry_id: int = 1):
    """Test returning panel bed by entry id."""

    # GIVEN a store with bed records

    # WHEN getting the query for the bed
    bed: Bed = base_store.get_bed_by_entry_id(entry_id)

    # THEN return a bed with the supplied bed id
    assert bed.id == entry_id


def test_get_bed_by_bed_name(base_store: Store, bed_name: str):
    """Test returning panel bed by name."""

    # GIVEN a store with bed records

    # WHEN getting the query for the bed
    bed: Bed = base_store.get_bed_by_name(bed_name)

    # THEN return a bed with the supplied bed id
    assert bed.name == bed_name


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
        base_store.session.add(bed)
        base_store.session.commit()

    # WHEN fetching beds
    active_beds: Query = base_store.get_active_beds()

    # THEN return no beds
    assert not list(active_beds)


def test_get_application_by_tag(microbial_store: Store, tag: str = MicrosaltAppTags.MWRNXTR003):
    """Test function to return the application by tag."""

    # GIVEN a store with application records

    # WHEN getting the query for the flow cells
    application: Application = microbial_store.get_application_by_tag(tag=tag)

    # THEN return a application with the supplied application tag
    assert application.tag == tag


def test_get_applications_is_not_archived(
    microbial_store: Store, EXPECTED_NUMBER_OF_NOT_ARCHIVED_APPLICATIONS
):
    """Test function to return the application when not archived."""

    # GIVEN a store with application records

    # WHEN getting the query for the flow cells
    applications: List[Application] = microbial_store.get_applications_is_not_archived()

    # THEN return a application with the supplied application tag
    assert len(applications) == EXPECTED_NUMBER_OF_NOT_ARCHIVED_APPLICATIONS
    assert (application.is_archived is False for application in applications)


def test_get_applications(microbial_store: Store, EXPECTED_NUMBER_OF_APPLICATIONS):
    """Test function to return the applications."""

    # GIVEN a store with application records

    # WHEN getting the query for the flow cells
    applications: List[Application] = microbial_store.get_applications()

    # THEN return a application with the supplied application tag
    assert len(applications) == EXPECTED_NUMBER_OF_APPLICATIONS


def test_get_bed_version_query(base_store: Store):
    """Test function to return the bed version query."""

    # GIVEN a store with bed versions records

    # WHEN getting the query for the bed versions
    bed_version_query: Query = base_store._get_query(table=BedVersion)

    # THEN a query should be returned
    assert isinstance(bed_version_query, Query)


def test_get_bed_version_by_file_name(base_store: Store, bed_version_file_name: str):
    """Test function to return the bed version by file name."""

    # GIVEN a store with bed versions records

    # WHEN getting the query for the bed versions
    bed_version: BedVersion = base_store.get_bed_version_by_file_name(
        bed_version_file_name=bed_version_file_name
    )

    # THEN return a bed version with the supplied bed version file_name
    assert bed_version.filename == bed_version_file_name


def test_get_bed_version_by_short_name(base_store: Store, bed_version_short_name: str):
    """Test function to return the bed version by short name."""

    # GIVEN a store with bed versions records

    # WHEN getting the query for the bed versions
    bed_version: BedVersion = base_store.get_bed_version_by_short_name(
        bed_version_short_name=bed_version_short_name
    )

    # THEN return a bed version with the supplied bed version short name
    assert bed_version.shortname == bed_version_short_name


def test_get_customer_by_internal_id(base_store: Store, customer_id: str):
    """Test function to return the customer by customer id."""

    # GIVEN a store with customer records

    # WHEN getting the query for the customer
    customer: Customer = base_store.get_customer_by_internal_id(customer_internal_id=customer_id)

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


def test_get_organism_by_internal_id_returns_correct_organism(store_with_organisms: Store):
    """Test finding an organism by internal ID when the ID exists."""

    # GIVEN a store with multiple organisms
    organisms: Query = store_with_organisms._get_query(table=Organism)
    assert organisms.count() > 0

    # GIVEN a random organism from the store
    organism: Organism = organisms.first()
    assert isinstance(organism, Organism)

    # WHEN finding the organism by internal ID
    filtered_organism = store_with_organisms.get_organism_by_internal_id(organism.internal_id)

    # THEN the filtered organism should be of instance Organism
    assert isinstance(filtered_organism, Organism)

    # THEN the filtered organism should match the database organism internal id
    assert filtered_organism.internal_id == organism.internal_id


def test_get_organism_by_internal_id_returns_none_when_id_does_not_exist(
    store_with_organisms: Store,
    non_existent_id: str,
):
    """Test finding an organism by internal ID when the ID does not exist."""

    # GIVEN a store with multiple organisms
    organisms: Query = store_with_organisms._get_query(table=Organism)
    assert organisms.count() > 0

    # WHEN finding the organism by internal ID that does not exist
    filtered_organism: Organism = store_with_organisms.get_organism_by_internal_id(
        internal_id=non_existent_id
    )

    # THEN the filtered organism should be None
    assert filtered_organism is None


def test_get_organism_by_internal_id_returns_none_when_id_is_none(
    store_with_organisms: Store,
):
    """Test finding an organism by internal ID None returns None."""

    # GIVEN a store with multiple organisms
    organisms: Query = store_with_organisms._get_query(table=Organism)
    assert organisms.count() > 0

    # WHEN finding the organism by internal ID None
    filtered_organism: Organism = store_with_organisms.get_organism_by_internal_id(internal_id=None)

    # THEN the filtered organism should be None
    assert filtered_organism is None


def test_get_user_by_email_returns_correct_user(store_with_users: Store):
    """Test fetching a user by email."""

    # GIVEN a store with multiple users
    num_users: int = store_with_users._get_query(table=User).count()
    assert num_users > 0

    # Select a random user from the store
    user: User = store_with_users._get_query(table=User).first()
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

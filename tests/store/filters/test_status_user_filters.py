from cg.store.filters.status_user_filters import filter_user_by_email
from cg.store.models import Customer, User
from cg.store.store import Store


def test_filter_user_by_email_returns_correct_user(store_with_users: Store):
    """Test getting user by email."""

    # GIVEN a store with a user
    user: User = store_with_users._get_query(table=User).first()
    assert user

    # WHEN retrieving the user by email
    filtered_user: User = filter_user_by_email(
        users=store_with_users._get_query(table=User),
        email=user.email,
    ).first()

    # THEN a user should be returned
    assert isinstance(filtered_user, User)

    # THEN the email should match
    assert filtered_user.email == user.email


def test_filter_user_by_email_returns_none_for_nonexisting_email(
    store_with_users: Store, non_existent_email: str
):
    """Test getting user by email when the email does not exist."""

    # GIVEN a non-existing email

    # WHEN retrieving the user by email
    filtered_user: User = filter_user_by_email(
        users=store_with_users._get_query(table=User),
        email=non_existent_email,
    ).first()

    # THEN no user should be returned
    assert filtered_user is None


def test_filter_user_by_email_none_returns_none(store_with_users: Store):
    """Test getting user by email None."""

    # WHEN retrieving the user by email None
    filtered_user: User = filter_user_by_email(
        users=store_with_users._get_query(table=User),
        email=None,
    ).first()

    # THEN no user should be returned
    assert filtered_user is None


def test_filter_user_by_customer(store_with_users: Store):

    # GIVEN a store with a user belonging to a customer
    user: User = store_with_users._get_query(table=User).first()
    customer: Customer = user.customers[0]

    # WHEN filtering the user by customer
    user_is_associated: bool = store_with_users.is_user_associated_with_customer(
        user_id=user.id,
        customer_internal_id=customer.internal_id,
    )

    # THEN the user should be associated with the customer
    assert user_is_associated


def test_filter_user_not_associated_with_customer(
    store_with_users: Store, customer_without_users: Customer
):

    # GIVEN a store with a user not belonging to a specific customer
    user: User = store_with_users._get_query(table=User).first()

    # WHEN filtering the user by customer
    user_is_associated: bool = store_with_users.is_user_associated_with_customer(
        user_id=user.id,
        customer_internal_id=customer_without_users.internal_id,
    )

    # THEN the user should not be associated with the customer
    assert not user_is_associated

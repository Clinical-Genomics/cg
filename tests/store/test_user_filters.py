from cg.store.api.core import Store
from cg.store.models import User
from cg.store.user_filters import filter_user_by_email


def test_filter_user_by_email_returns_correct_user(store_with_users: Store):
    """Test getting user by email."""

    # GIVEN a store with a user
    user: User = store_with_users._get_user_query().first()
    assert user

    user_email: str = user.email

    # WHEN retrieving the user by email
    filtered_user: User = filter_user_by_email(
        users=store_with_users._get_user_query(),
        email=user_email,
    ).first()

    # THEN a user should be returned
    assert isinstance(filtered_user, User)

    # THEN the email should match
    assert filtered_user.email == user_email


def test_filter_user_by_email_returns_none_for_nonexisting_email(store_with_users: Store):
    """Test getting user by email when the email does not exist."""

    # GIVEN a non-existing email
    non_existent_email = "non_existing@example.com"

    # WHEN retrieving the user by email
    filtered_user: User = filter_user_by_email(
        users=store_with_users._get_user_query(),
        email=non_existent_email,
    ).first()

    # THEN no user should be returned
    assert filtered_user is None

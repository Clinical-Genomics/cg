from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import Customer, User


def filter_user_by_email(users: Query, email: str, **kwargs) -> Query:
    """Return user by email."""
    return users.filter(User.email == email)


def filter_user_by_id(users: Query, user_id: int, **kwargs) -> Query:
    return users.filter(User.id == user_id)


def filter_user_by_customer_internal_id(users: Query, customer_internal_id: str, **kwargs) -> Query:
    return users.join(User.customers).filter(Customer.internal_id == customer_internal_id)


class UserFilter(Enum):
    """Define User filter functions."""

    BY_EMAIL: Callable = filter_user_by_email
    BY_ID: Callable = filter_user_by_id
    BY_CUSTOMER_INTERNAL_ID: Callable = filter_user_by_customer_internal_id


def apply_user_filter(
    users: Query,
    filter_functions: list[Callable],
    email: str | None = None,
    user_id: int | None = None,
    customer_internal_id: str | None = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for filter_function in filter_functions:
        users: Query = filter_function(
            users=users,
            email=email,
            user_id=user_id,
            customer_internal_id=customer_internal_id,
        )
    return users

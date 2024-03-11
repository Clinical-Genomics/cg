from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import User


def filter_user_by_email(users: Query, email: str, **kwargs) -> Query:
    """Return user by email."""
    return users.filter(User.email == email)


class UserFilter(Enum):
    """Define User filter functions."""

    BY_EMAIL: Callable = filter_user_by_email


def apply_user_filter(
    users: Query,
    filter_functions: list[Callable],
    email: str | None = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for filter_function in filter_functions:
        users: Query = filter_function(
            users=users,
            email=email,
        )
    return users

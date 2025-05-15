from cg.store.models import User
from cg.store.store import Store


class UserService:
    """Service to handle user related operations."""

    def __init__(self, store: Store):
        self.store = store

    def get_user_by_email(self, email: str):
        """
        Get user by email.
        args:
            email: str
        returns:
            User
        raises:
            ValueError: if the user is not found
        """
        user: User | None = self.store.get_user_by_email(email)
        if not user:
            raise ValueError(f"User with email {email} not found")
        return user

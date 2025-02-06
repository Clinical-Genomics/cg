from cg.services.user.constants import ADMIN, CUSTOMER
from cg.services.user.models import AuthenticatedUser
from cg.store.models import User
from cg.store.store import Store


class UserService:
    """Service to handle user related operations."""
    
    
    def __init__(self, store:  Store):
        self.store = store
        
    def _get_user_by_email(self, email: str):
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
    
    def _check_role(self, user: User) -> str:
        """
        Check if user has the role.
        args:
            user: User
        returns:
            str
        raises:
            ValueError: if the user does not have access
        """
        if user.is_admin:
            return ADMIN
        if user.order_portal_login:
            return CUSTOMER
        raise ValueError('User does not have access')  

    def get_authenticated_user(self, email: str) -> AuthenticatedUser:
        """
        Get user response.
        args:
            email: str
        returns:
            AuthenticatedUser
        """
        user = self._get_user_by_email(email)
        role: str = self._check_role(user)
        return AuthenticatedUser(
            id=user.id,
            name=user.name,
            email=user.email,
            role=role,
        )
        
  
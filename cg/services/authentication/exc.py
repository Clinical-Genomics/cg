from cg.exc import CgError


class TokenIntrospectionError(ValueError):
    pass


class UserRoleError(CgError):
    pass


class UserNotFoundError(CgError):
    pass

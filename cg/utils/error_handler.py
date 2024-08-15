"""Module that holds a generic error handling decorator."""

from cg.exc import CgError


def handle_errors(to_except: tuple, to_raise):
    """Handle errors for the Post processing services."""

    def error_handling(fn):
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except to_except as error:
                raise to_raise(error) from error
            except Exception as error:
                raise CgError(f"{error}") from error

        return wrapper

    return error_handling

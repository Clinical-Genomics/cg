import operator

from cg.exc import CgError


def validate_operator(norm: str) -> str:
    """Validate that an operator is accepted."""
    try:
        getattr(operator, norm)
    except AttributeError as error:
        raise CgError(f"{norm} is not an accepted operator for QC metric conditions.") from error
    return norm

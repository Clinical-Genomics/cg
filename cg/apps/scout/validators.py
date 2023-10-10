from typing import Optional

from cg.constants.subject import Gender, PlinkGender, RelationshipStatus


def set_parent_if_missing(parent: Optional[str]) -> str:
    return RelationshipStatus.HAS_NO_PARENT if parent is None else parent


def set_gender_if_other(gender: Optional[str]) -> str:
    return PlinkGender.UNKNOWN if gender == Gender.OTHER else gender

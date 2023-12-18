from cg.constants.gene_panel import GENOME_BUILD_37
from cg.constants.subject import PlinkSex, RelationshipStatus, Sex


def convert_genome_build(value):
    return GENOME_BUILD_37 if value is None else value


def set_parent_if_missing(parent: str | None) -> str:
    return RelationshipStatus.HAS_NO_PARENT if parent is None else parent


def set_gender_if_other(gender: str | None) -> str:
    return PlinkSex.UNKNOWN if gender == Sex.OTHER else gender

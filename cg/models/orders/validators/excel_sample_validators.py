from typing import Optional

from cg.constants.orderforms import REV_SEX_MAP, SOURCE_TYPES
from cg.models.orders.sample_base import PriorityEnum


def parse_panels(panels: str) -> Optional[list[str]]:
    if not panels:
        return None
    separator = ";" if ";" in panels else None
    if ":" in panels:
        separator = ":"
    return panels.split(separator)


def validate_data_analysis(data_analysis):
    data_analysis_alternatives = [
        "Balsamic",  # OF 1508
        "Balsamic QC",  # OF 1508
        "Balsamic UMI",  # OF 1508
        "fastq",  # OF 1605
        "FLUFFY",  # OF 1604
        "MicroSALT",  # OF 1603 (implicit)
        "MIP DNA",  # OF 1508
        "MIP RNA",  # OF 1508
        "RNAfusion",  # OF 1508
        "SARS-CoV-2",  # OF 2184
        "No analysis",  # OF 1508, 1604, 2184
    ]
    if data_analysis not in data_analysis_alternatives:
        raise AttributeError(f"'{data_analysis}' is not a valid data analysis")
    return data_analysis


def numeric_value(value: Optional[str]) -> Optional[str]:
    """Validates that the given string can be given as either an integer or a float. Also converts floats of the
    type x.00 to x."""
    if not value:
        return None
    try:
        float_value: float = float(value)
        if float_value.is_integer():
            return str(int(float_value))
        return value
    except ValueError:
        raise AttributeError(f"Order contains non-numeric value '{value}'")


def validate_parent(parent: str) -> str:
    return None if parent == "0.0" else parent


def validate_source(source: Optional[str]) -> str:
    if source not in SOURCE_TYPES:
        raise ValueError(f"'{source}' is not a valid source")
    return source


def convert_sex(sex: str) -> Optional[str]:
    if not sex:
        return None
    sex = sex.strip()
    return REV_SEX_MAP.get(sex, "unknown")


def convert_to_lower(value: str) -> str:
    return value.lower()


def replace_spaces_with_underscores(value: str) -> str:
    return value.replace(" ", "_")


def convert_to_priority(priority: Optional[str]) -> Optional[str]:
    """Translates the Swedish 'förtur' to 'priority' if specified in the order."""
    return PriorityEnum.priority if priority == "förtur" else priority


def convert_to_date(date: Optional[str]) -> Optional[str]:
    return date[:10] if date else None

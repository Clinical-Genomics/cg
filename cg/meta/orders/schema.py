from collections import Iterable
from cg.utils.StrEnum import StrEnum
from pyschemes import Scheme, validators

from cg.constants import (
    PRIORITY_OPTIONS,
    SEX_OPTIONS,
    STATUS_OPTIONS,
    CAPTUREKIT_OPTIONS,
    CONTAINER_OPTIONS,
    Pipeline,
)


class OrderType(StrEnum):
    BALSAMIC: str = str(Pipeline.BALSAMIC)
    EXTERNAL: str = "external"
    FASTQ: str = "fastq"
    METAGENOME: str = "metagenome"
    MICROSALT: str = str(Pipeline.MICROSALT)
    MIP_DNA: str = str(Pipeline.MIP_DNA)
    MIP_RNA: str = str(Pipeline.MIP_RNA)
    RML: str = "rml"


class ListValidator(validators.Validator):

    """Validate a list of items against a schema."""

    def __init__(self, scheme: validators.Validator, min_items: int = 0):
        super().__init__(scheme)
        self.__scheme = validators.Validator.create_validator(scheme)
        self.min_items = min_items

    def validate(self, value: Iterable):
        """Validate the list of values."""
        values = value
        validators.TypeValidator(Iterable).validate(values)
        values_copy = []
        for one_value in values:
            self.__scheme.validate(one_value)
            values_copy.append(one_value)
        if len(values_copy) < self.min_items:
            raise ValueError(f"value did not contain at least {self.min_items} items")
        return values_copy


class TypeValidatorNone(validators.TypeValidator):
    """Type Scheme that accepts None."""

    def validate(self, value):
        """Validate the type of the value, accept None"""
        if value in (None, ""):
            return value
        return super().validate(value)


class RegexValidatorNone(validators.RegexValidator):
    """Validator for regex patterns that accepts None."""

    def validate(self, value):
        """Validate the the value against an regular expression, accept None"""
        if value in (None, ""):
            return value
        return super().validate(value)


class OptionalNone(validators.Optional):
    """Optional Scheme that accepts None."""

    def __init__(self, scheme, default=None):
        super().__init__(scheme, default)

    def validate(self, *value):
        """Validate the value with the given validator, accept missing values, accept None"""
        if value:
            val = value[0]

            if val in (None, ""):
                return val

            return super().validate(val)
        return self.default


NAME_PATTERN = r"^[A-Za-z0-9-]*$"

BASE_PROJECT = {"name": str, "customer": str, "comment": OptionalNone(TypeValidatorNone(str))}

MIP_SAMPLE = {
    # Orderform 1508:18
    # Order portal specific
    "internal_id": OptionalNone(TypeValidatorNone(str)),
    # "required for new samples"
    "name": validators.RegexValidator(NAME_PATTERN),
    # customer
    "data_analysis": str,
    "data_delivery": OptionalNone(TypeValidatorNone(str)),
    "application": str,
    "family_name": validators.RegexValidator(NAME_PATTERN),
    "sex": OptionalNone(validators.Any(SEX_OPTIONS)),
    "tumour": bool,
    "source": OptionalNone(TypeValidatorNone(str)),
    "priority": OptionalNone(validators.Any(PRIORITY_OPTIONS)),
    "require_qcok": bool,
    "container": OptionalNone(validators.Any(CONTAINER_OPTIONS)),
    # "required if plate for new samples"
    "container_name": OptionalNone(TypeValidatorNone(str)),
    "well_position": OptionalNone(TypeValidatorNone(str)),
    # "Required if data analysis in Scout or vcf delivery"
    "panels": ListValidator(str, min_items=1),
    "status": OptionalNone(validators.Any(STATUS_OPTIONS)),
    # "Required if samples are part of trio/family"
    "mother": OptionalNone(RegexValidatorNone(NAME_PATTERN)),
    "father": OptionalNone(RegexValidatorNone(NAME_PATTERN)),
    # This information is required for panel analysis
    "capture_kit": OptionalNone(TypeValidatorNone(str)),
    # This information is required for panel- or exome analysis
    "elution_buffer": OptionalNone(TypeValidatorNone(str)),
    "tumour_purity": OptionalNone(TypeValidatorNone(str)),
    # "This information is optional for FFPE-samples for new samples"
    "formalin_fixation_time": OptionalNone(TypeValidatorNone(str)),
    "post_formalin_fixation_time": OptionalNone(TypeValidatorNone(str)),
    "tissue_block_size": OptionalNone(TypeValidatorNone(str)),
    # "Not Required"
    "quantity": OptionalNone(TypeValidatorNone(str)),
    "comment": OptionalNone(TypeValidatorNone(str)),
}

BALSAMIC_SAMPLE = {
    # 1508:18 Orderform
    # Order portal specific
    "internal_id": OptionalNone(TypeValidatorNone(str)),
    # "This information is required for new samples"
    "name": validators.RegexValidator(NAME_PATTERN),
    "container": OptionalNone(validators.Any(CONTAINER_OPTIONS)),
    "data_analysis": str,
    "data_delivery": OptionalNone(TypeValidatorNone(str)),
    "application": str,
    "sex": OptionalNone(validators.Any(SEX_OPTIONS)),
    "family_name": validators.RegexValidator(NAME_PATTERN),
    "require_qcok": bool,
    "tumour": bool,
    "source": OptionalNone(TypeValidatorNone(str)),
    "priority": OptionalNone(validators.Any(PRIORITY_OPTIONS)),
    # Required if Plate for new samples
    "container_name": OptionalNone(TypeValidatorNone(str)),
    "well_position": OptionalNone(TypeValidatorNone(str)),
    # This information is required for panel analysis
    "capture_kit": OptionalNone(TypeValidatorNone(str)),
    # This information is required for panel- or exome analysis
    "elution_buffer": OptionalNone(TypeValidatorNone(str)),
    "tumour_purity": OptionalNone(TypeValidatorNone(str)),
    # This information is optional for FFPE-samples for new samples
    "formalin_fixation_time": OptionalNone(TypeValidatorNone(str)),
    "post_formalin_fixation_time": OptionalNone(TypeValidatorNone(str)),
    "tissue_block_size": OptionalNone(TypeValidatorNone(str)),
    # This information is optional
    "quantity": OptionalNone(TypeValidatorNone(str)),
    "comment": OptionalNone(TypeValidatorNone(str)),
}

MIP_RNA_SAMPLE = {
    "internal_id": OptionalNone(TypeValidatorNone(str)),
    # "required for new samples"
    "name": validators.RegexValidator(NAME_PATTERN),
    # customer
    "data_analysis": str,
    "data_delivery": OptionalNone(TypeValidatorNone(str)),
    "application": str,
    "family_name": validators.RegexValidator(NAME_PATTERN),
    "sex": OptionalNone(validators.Any(SEX_OPTIONS)),
    "source": OptionalNone(TypeValidatorNone(str)),
    "priority": OptionalNone(validators.Any(PRIORITY_OPTIONS)),
    "container": OptionalNone(validators.Any(CONTAINER_OPTIONS)),
    # "required if plate for new samples"
    "container_name": OptionalNone(TypeValidatorNone(str)),
    "well_position": OptionalNone(TypeValidatorNone(str)),
    "formalin_fixation_time": OptionalNone(TypeValidatorNone(str)),
    "post_formalin_fixation_time": OptionalNone(TypeValidatorNone(str)),
    "tissue_block_size": OptionalNone(TypeValidatorNone(str)),
    # # "Not Required"
    "quantity": OptionalNone(TypeValidatorNone(str)),
    "comment": OptionalNone(TypeValidatorNone(str)),
    # Orderform 1508:19
    "from_sample": validators.RegexValidator(NAME_PATTERN),
    "time_point": OptionalNone(TypeValidatorNone(str)),
}

EXTERNAL_SAMPLE = {
    # Orderform 1541:6
    # Order portal specific
    "internal_id": OptionalNone(TypeValidatorNone(str)),
    "data_analysis": str,
    "data_delivery": OptionalNone(TypeValidatorNone(str)),
    # "required for new samples"
    "name": validators.RegexValidator(NAME_PATTERN),
    "capture_kit": OptionalNone(TypeValidatorNone(str)),
    "application": str,
    "sex": OptionalNone(validators.Any(SEX_OPTIONS)),
    "family_name": validators.RegexValidator(NAME_PATTERN),
    "priority": OptionalNone(validators.Any(PRIORITY_OPTIONS)),
    "source": OptionalNone(TypeValidatorNone(str)),
    # "Required if data analysis in Scout"
    "panels": ListValidator(str, min_items=0),
    # todo: find out if "Additional Gene List" is "lost in translation", implement in OP or remove from OF
    "status": OptionalNone(validators.Any(STATUS_OPTIONS)),
    # "Required if samples are part of trio/family"
    "mother": OptionalNone(RegexValidatorNone(NAME_PATTERN)),
    "father": OptionalNone(RegexValidatorNone(NAME_PATTERN)),
    # todo: find out if "Other relations" is removed in current OF
    # "Not Required"
    "tumour": OptionalNone(bool, False),
    # todo: find out if "Gel picture" is "lost in translation", implement in OP or remove from OF
    "extraction_method": OptionalNone(TypeValidatorNone(str)),
    "comment": OptionalNone(TypeValidatorNone(str)),
}

FASTQ_SAMPLE = {
    # Orderform 1508:?
    # "required"
    "name": validators.RegexValidator(NAME_PATTERN),
    "container": OptionalNone(validators.Any(CONTAINER_OPTIONS)),
    "data_analysis": str,
    "data_delivery": OptionalNone(TypeValidatorNone(str)),
    "application": str,
    "sex": OptionalNone(validators.Any(SEX_OPTIONS)),
    # todo: implement in OP or remove from OF
    # 'family_name': RegexValidator(NAME_PATTERN),
    "require_qcok": bool,
    "source": str,
    "tumour": bool,
    "priority": OptionalNone(validators.Any(PRIORITY_OPTIONS)),
    # "required if plate"
    "container_name": OptionalNone(TypeValidatorNone(str)),
    "well_position": OptionalNone(TypeValidatorNone(str)),
    # "Required if data analysis in Scout or vcf delivery" => not valid for fastq
    # 'panels': ListValidator(str, min_items=1),
    # 'status': OptionalNone(validators.Any(STATUS_OPTIONS),
    "elution_buffer": str,
    # "Required if samples are part of trio/family"
    "mother": OptionalNone(RegexValidatorNone(NAME_PATTERN)),
    "father": OptionalNone(RegexValidatorNone(NAME_PATTERN)),
    # "Not Required"
    "quantity": OptionalNone(TypeValidatorNone(str)),
    "comment": OptionalNone(TypeValidatorNone(str)),
}

RML_SAMPLE = {
    # 1604:9 Orderform Ready made libraries (RML)
    # Order portal specific
    "priority": str,
    # "This information is required"
    "name": validators.RegexValidator(NAME_PATTERN),
    "pool": str,
    "application": str,
    "data_analysis": str,
    "data_delivery": OptionalNone(TypeValidatorNone(str)),
    "volume": str,
    "concentration": str,
    "index": str,
    "index_number": OptionalNone(TypeValidatorNone(str)),  # optional for NoIndex
    # "Required if Plate"
    "rml_plate_name": OptionalNone(TypeValidatorNone(str)),
    "well_position_rml": OptionalNone(TypeValidatorNone(str)),
    # "Automatically generated (if not custom) or custom"
    "index_sequence": OptionalNone(TypeValidatorNone(str)),
    # "Not required"
    "comment": OptionalNone(TypeValidatorNone(str)),
    "capture_kit": OptionalNone(validators.Any(CAPTUREKIT_OPTIONS)),
}

MICROSALT_SAMPLE = {
    # 1603:6 Orderform Microbial WGS
    # "These fields are required"
    "name": validators.RegexValidator(NAME_PATTERN),
    "organism": str,
    "reference_genome": str,
    "data_analysis": str,
    "data_delivery": OptionalNone(TypeValidatorNone(str)),
    "application": str,
    "require_qcok": bool,
    "elution_buffer": str,
    "extraction_method": str,
    "container": OptionalNone(validators.Any(CONTAINER_OPTIONS)),
    "priority": OptionalNone(validators.Any(PRIORITY_OPTIONS)),
    # "Required if Plate"
    "container_name": OptionalNone(TypeValidatorNone(str)),
    "well_position": OptionalNone(TypeValidatorNone(str)),
    # "Required if "Other" is chosen in column "Species""
    "organism_other": OptionalNone(TypeValidatorNone(str)),
    # "These fields are not required"
    "concentration_weight": OptionalNone(TypeValidatorNone(str)),
    "quantity": OptionalNone(TypeValidatorNone(str)),
    "comment": OptionalNone(TypeValidatorNone(str)),
}

METAGENOME_SAMPLE = {
    # 1605:4 Orderform Microbial Metagenomes- 16S
    # "This information is required"
    "name": validators.RegexValidator(NAME_PATTERN),
    "container": OptionalNone(validators.Any(CONTAINER_OPTIONS)),
    "data_analysis": str,
    "data_delivery": OptionalNone(TypeValidatorNone(str)),
    "application": str,
    "require_qcok": bool,
    "elution_buffer": str,
    "source": str,
    "priority": OptionalNone(validators.Any(PRIORITY_OPTIONS)),
    # "Required if Plate"
    "container_name": OptionalNone(TypeValidatorNone(str)),
    "well_position": OptionalNone(TypeValidatorNone(str)),
    # "This information is not required"
    "concentration_weight": OptionalNone(TypeValidatorNone(str)),
    "quantity": OptionalNone(TypeValidatorNone(str)),
    "extraction_method": OptionalNone(TypeValidatorNone(str)),
    "comment": OptionalNone(TypeValidatorNone(str)),
}

ORDER_SCHEMES = {
    OrderType.EXTERNAL: Scheme(
        {**BASE_PROJECT, "samples": ListValidator(EXTERNAL_SAMPLE, min_items=1)}
    ),
    OrderType.MIP_DNA: Scheme({**BASE_PROJECT, "samples": ListValidator(MIP_SAMPLE, min_items=1)}),
    OrderType.BALSAMIC: Scheme(
        {**BASE_PROJECT, "samples": ListValidator(BALSAMIC_SAMPLE, min_items=1)}
    ),
    OrderType.MIP_RNA: Scheme(
        {**BASE_PROJECT, "samples": ListValidator(MIP_RNA_SAMPLE, min_items=1)}
    ),
    OrderType.FASTQ: Scheme({**BASE_PROJECT, "samples": ListValidator(FASTQ_SAMPLE, min_items=1)}),
    OrderType.RML: Scheme({**BASE_PROJECT, "samples": ListValidator(RML_SAMPLE, min_items=1)}),
    OrderType.MICROSALT: Scheme(
        {**BASE_PROJECT, "samples": ListValidator(MICROSALT_SAMPLE, min_items=1)}
    ),
    OrderType.METAGENOME: Scheme(
        {**BASE_PROJECT, "samples": ListValidator(METAGENOME_SAMPLE, min_items=1)}
    ),
}

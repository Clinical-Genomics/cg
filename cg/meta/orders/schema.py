from collections import Iterable
from enum import Enum

from pyschemes import Scheme, validators

from cg.constants import PRIORITY_OPTIONS, SEX_OPTIONS, STATUS_OPTIONS, CAPTUREKIT_OPTIONS


class OrderType(Enum):
    EXTERNAL = 'external'
    FASTQ = 'fastq'
    RML = 'rml'
    SCOUT = 'scout'
    MICROBIAL = 'microbial'
    METAGENOME = 'metagenome'


class ListValidator(validators.Validator):

    """Validate a list of items against a schema."""

    def __init__(self, scheme: validators.Validator, min_items: int=0):
        super(ListValidator, self).__init__(scheme)
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


class TypeValidator(validators.Validator):

    def __init__(self, _type, allow_none=False):
        self._type = _type
        self.allow_none = allow_none

    def validate(self, value):
        if isinstance(value, self._type) or (self.allow_none and value is None):
            return value
        else:
            message = f"expected type: '{self._type.__name__}', got '{type(value).__name__}'"
            raise TypeError(message)


NAME_PATTERN = r'^[A-Za-z0-9-]*$'

BASE_PROJECT = {
    'name': str,
    'customer': str,
    'comment': validators.Optional(TypeValidator(str, allow_none=True), None),
}

BASE_SAMPLE = {
    'name': validators.RegexValidator(NAME_PATTERN),
    'internal_id': validators.Optional(TypeValidator(str, allow_none=True), None),
    'application': str,
    'comment': validators.Optional(TypeValidator(str, allow_none=True), None),
}

PREP_MIXIN = {
    'well_position': validators.Optional(TypeValidator(str, allow_none=True), None),
    'tumour': validators.Optional(bool, False),
    'source': validators.Optional(TypeValidator(str, allow_none=True), None),
    'priority': validators.Optional(validators.Any(PRIORITY_OPTIONS), 'standard'),
    'require_qcok': validators.Optional(bool, False),
}

LAB_MIXIN = {
    'container': validators.Optional(str, 'Tube'),
    'container_name':  validators.Optional(str, None),
    'quantity': validators.Optional(str, None),
    'volume': validators.Optional(TypeValidator(str, allow_none=True), None),
    'concentration': validators.Optional(TypeValidator(str, allow_none=True), None),
}

ANALYSIS_MIXIN = {
    'status': validators.Any(STATUS_OPTIONS),
    'family_name': validators.RegexValidator(NAME_PATTERN),
    'panels': ListValidator(str, min_items=1),
    'father': validators.Optional(TypeValidator(str, allow_none=True), None),
    'mother': validators.Optional(TypeValidator(str, allow_none=True), None),
    'sex': validators.Any(SEX_OPTIONS),
}

SCOUT_SAMPLE = {**BASE_SAMPLE, **LAB_MIXIN, **PREP_MIXIN, **ANALYSIS_MIXIN}

EXTERNAL_SAMPLE = {
    **BASE_SAMPLE,
    **ANALYSIS_MIXIN,
    'capture_kit': validators.Optional(validators.Any(CAPTUREKIT_OPTIONS), None),
}

FASTQ_SAMPLE = {
    **BASE_SAMPLE,
    **LAB_MIXIN,
    **PREP_MIXIN,
    'sex': validators.Any(SEX_OPTIONS),
}

RML_SAMPLE = {
    **BASE_SAMPLE,
    **LAB_MIXIN,
    'pool': str,
    'well_position_rml': validators.Optional(TypeValidator(str, allow_none=True), None),
    'rml_plate_name': validators.Optional(TypeValidator(str, allow_none=True), None),
    'index': validators.Optional(TypeValidator(str, allow_none=True), None),
    'index_number': validators.Optional(TypeValidator(str, allow_none=True), None),
    'index_sequence': validators.Optional(TypeValidator(str, allow_none=True), None),
    'capture_kit': validators.Optional(TypeValidator(str, allow_none=True), None),
}

MICROBIAL_SAMPLE = {
    **BASE_SAMPLE,
    **LAB_MIXIN,
    **PREP_MIXIN,
    'organism': str,
    'organism_other': validators.Optional(str, None),
    'reference_genome': str,
    'verified_organism': bool,
    'elution_buffer': str,
    'extraction_method': str,
    'concentration_weight': validators.Optional(TypeValidator(str, allow_none=True), None),
}

METAGENOME_SAMPLE = {
    **BASE_SAMPLE,
    **LAB_MIXIN,
    **PREP_MIXIN,
    'source': validators.Optional(str, None),
    'elution_buffer': str,
    'extraction_method': validators.Optional(str, None),
    'concentration_weight': validators.Optional(TypeValidator(str, allow_none=True), None),
}

ORDER_SCHEMES = {
    OrderType.EXTERNAL: Scheme({
        **BASE_PROJECT,
        'samples': ListValidator(EXTERNAL_SAMPLE, min_items=1)
    }),
    OrderType.SCOUT: Scheme({
        **BASE_PROJECT,
        'samples': ListValidator(SCOUT_SAMPLE, min_items=1)
    }),
    OrderType.FASTQ: Scheme({
        **BASE_PROJECT,
        'samples': ListValidator(FASTQ_SAMPLE, min_items=1),
    }),
    OrderType.RML: Scheme({
        **BASE_PROJECT,
        'samples': ListValidator(RML_SAMPLE, min_items=1),
    }),
    OrderType.MICROBIAL: Scheme({
        **BASE_PROJECT,
        'samples': ListValidator(MICROBIAL_SAMPLE, min_items=1),
    }),
    OrderType.METAGENOME: Scheme({
        **BASE_PROJECT,
        'samples': ListValidator(METAGENOME_SAMPLE, min_items=1),
    }),
}

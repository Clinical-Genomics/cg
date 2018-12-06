from collections import Iterable
from enum import Enum

from pyschemes import Scheme, validators

from cg.constants import PRIORITY_OPTIONS, SEX_OPTIONS, STATUS_OPTIONS, CAPTUREKIT_OPTIONS, \
    CONTAINER_OPTIONS, CAPTUREKIT_CANCER_OPTIONS


class OrderType(Enum):
    EXTERNAL = 'external'
    FASTQ = 'fastq'
    RML = 'rml'
    MIP = 'mip'
    MICROBIAL = 'microbial'
    METAGENOME = 'metagenome'
    BALSAMIC = 'balsamic'
    MIP_BALSAMIC = 'mip_balsamic'


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

MIP_SAMPLE = {
    # Orderform 1508:12

    # Order portal specific
    'internal_id': validators.Optional(TypeValidator(str, allow_none=True), None),

    # required
    'name': validators.RegexValidator(NAME_PATTERN),
    'container': validators.Optional(str, None),
    'data_analysis': str,
    'application': str,
    'sex': validators.Any(SEX_OPTIONS),
    'family_name': validators.RegexValidator(NAME_PATTERN),
    'require_qcok': bool,
    'source': validators.Optional(str, None),
    'tumour': bool,
    'priority': validators.Any(PRIORITY_OPTIONS),

    # required if plate
    'container_name': validators.Optional(str, None),
    'well_position': validators.Optional(TypeValidator(str, allow_none=True), None),

    # Required if data analysis in Scout or vcf delivery
    'panels': ListValidator(str, min_items=1),
    'status': validators.Any(STATUS_OPTIONS),

    # Required if samples are part of trio/family
    'mother': validators.Optional(TypeValidator(str, allow_none=True), None),
    'father': validators.Optional(TypeValidator(str, allow_none=True), None),

    # This information is optional for FFPE-samples
    'formalin_fixation_time': validators.Optional(str, None),
    'post_formalin_fixation_time': validators.Optional(str, None),
    'tissue_block_size': validators.Optional(str, None),

    # Not Required
    'quantity': validators.Optional(str, None),
    'comment': validators.Optional(TypeValidator(str, allow_none=True), None),
}

BALSAMIC_SAMPLE = {
    # 1508:14 Orderform

    # Order portal specific
    'internal_id': validators.Optional(TypeValidator(str, allow_none=True), None),

    # This information is required
    'name': validators.RegexValidator(NAME_PATTERN),
    'container': validators.Optional(TypeValidator(str, allow_none=True), None),
    'data_analysis': str,
    'application': str,
    'sex': validators.Any(SEX_OPTIONS),
    'family_name': validators.RegexValidator(NAME_PATTERN),
    'require_qcok': bool,
    'tumour': bool,
    'source': validators.Optional(TypeValidator(str, allow_none=True), None),
    'priority': validators.Any(PRIORITY_OPTIONS),

    # Required if Plate
    'container_name': validators.Optional(str, None),
    'well_position': validators.Optional(TypeValidator(str, allow_none=True), None),

    # This information is required for Balsamic analysis (cancer)
    'capture_kit': validators.Optional(TypeValidator(str, allow_none=True), None),
    'tumour_purity': validators.Optional(str, None),

    # This information is optional for FFPE-samples
    'formalin_fixation_time': validators.Optional(str, None),
    'post_formalin_fixation_time': validators.Optional(str, None),
    'tissue_block_size': validators.Optional(str, None),

    # This information is optional
    'quantity': validators.Optional(str, None),
    'comment': validators.Optional(TypeValidator(str, allow_none=True), None),
}

MIP_BALSAMIC_SAMPLE = {
    **BALSAMIC_SAMPLE,
    **MIP_SAMPLE,
}

EXTERNAL_SAMPLE = {
    # Orderform 1541:6

    # Order portal specific
    'internal_id': validators.Optional(TypeValidator(str, allow_none=True), None),
    'data_analysis': str,

    # required
    'name': validators.RegexValidator(NAME_PATTERN),
    'capture_kit': validators.Optional(TypeValidator(str, allow_none=True), None),
    'application': str,
    'sex': validators.Any(SEX_OPTIONS),
    'family_name': validators.RegexValidator(NAME_PATTERN),
    'priority': validators.Any(PRIORITY_OPTIONS),
    'source': validators.Optional(TypeValidator(str, allow_none=True), None),

    # Required if data analysis in Scout
    'panels': ListValidator(str, min_items=0),
    # todo: find out if "Additional Gene List" is "lost in translation", implement in OP or remove from OF
    'status': validators.Any(STATUS_OPTIONS),

    # Required if samples are part of trio/family
    'mother': validators.Optional(TypeValidator(str, allow_none=True), None),
    'father': validators.Optional(TypeValidator(str, allow_none=True), None),
    # todo: find out if "Other relations" is removed in current OF

    # Not Required
    'tumour': validators.Optional(bool, False),
    # todo: find out if "Gel picture" is "lost in translation", implement in OP or remove from OF
    'extraction_method': validators.Optional(str, None),
    'comment': validators.Optional(TypeValidator(str, allow_none=True), None),
}

FASTQ_SAMPLE = {
    # Orderform 1508:12

    # required
    'name': validators.RegexValidator(NAME_PATTERN),
    'container': validators.Any(CONTAINER_OPTIONS),
    'data_analysis': str,
    'application': str,
    'sex': validators.Any(SEX_OPTIONS),
    # todo: implement in OP or remove from OF
    # 'family_name': validators.RegexValidator(NAME_PATTERN),
    'require_qcok': bool,
    'source': str,
    'tumour': bool,
    'priority': validators.Any(PRIORITY_OPTIONS),

    # required if plate
    'container_name': validators.Optional(str, None),
    'well_position': validators.Optional(TypeValidator(str, allow_none=True), None),

    # Required if data analysis in Scout or vcf delivery => not valid for fastq
    # 'panels': ListValidator(str, min_items=1),
    # 'status': validators.Any(STATUS_OPTIONS),

    # Required if samples are part of trio/family
    'mother': validators.Optional(validators.RegexValidator(NAME_PATTERN), None),
    'father': validators.Optional(validators.RegexValidator(NAME_PATTERN), None),

    # Not Required
    'quantity': validators.Optional(str, None),
    'comment': validators.Optional(TypeValidator(str, allow_none=True), None),
}

RML_SAMPLE = {
    # 1604:8 Orderform Ready made libraries (RML)

    # Order portal specific
    'priority': str,

    # This information is required
    'name': validators.RegexValidator(NAME_PATTERN),
    'pool': str,
    'application': str,
    'data_analysis': str,
    # todo: implement in OP or remove from OF
    # 'family_name': validators.RegexValidator(NAME_PATTERN),
    'volume': str,
    'concentration': str,
    'index': str,
    'index_number': str,

    # Required if Plate
    'rml_plate_name': validators.Optional(TypeValidator(str, allow_none=True), None),
    'well_position_rml': validators.Optional(TypeValidator(str, allow_none=True), None),

    # Automatically generated (if not custom) or custom
    'index_sequence': validators.Optional(TypeValidator(str, allow_none=True), None),

    # Not required
    'comment': validators.Optional(TypeValidator(str, allow_none=True), None),
    'capture_kit': validators.Optional(TypeValidator(str, allow_none=True), None),
}

MICROBIAL_SAMPLE = {
    # 1603:6 Orderform Microbial WGS

    # These fields are required
    'name': validators.RegexValidator(NAME_PATTERN),
    'organism': str,
    'reference_genome': str,
    'data_analysis': str,
    'application': str,
    'require_qcok': bool,
    'elution_buffer': str,
    'extraction_method': str,
    'container': validators.Any(CONTAINER_OPTIONS),
    'priority': validators.Any(PRIORITY_OPTIONS),

    # Required if Plate
    'container_name': validators.Optional(str, None),
    'well_position': validators.Optional(TypeValidator(str, allow_none=True), None),

    # Required if "Other" is chosen in column "Species"
    'organism_other': validators.Optional(str, None),

    # Required if "other" is chosen in column "DNA Elution Buffer"
    'elution_buffer_other': validators.Optional(str, None),

    # These fields are not required
    'concentration_weight': validators.Optional(TypeValidator(str, allow_none=True), None),
    'quantity': validators.Optional(str, None),
    'comment': validators.Optional(TypeValidator(str, allow_none=True), None),
}

METAGENOME_SAMPLE = {
    # 1605:4 Orderform Microbial Metagenomes- 16S

    # This information is required
    'name': validators.RegexValidator(NAME_PATTERN),
    'container': validators.Any(CONTAINER_OPTIONS),
    'data_analysis': str,
    'application': str,
    'require_qcok': bool,
    'elution_buffer': str,
    'source': str,
    'priority': validators.Any(PRIORITY_OPTIONS),

    # Required if Plate
    'container_name': validators.Optional(str, None),
    'well_position': validators.Optional(TypeValidator(str, allow_none=True), None),

    # This information is not required
    'concentration_weight': validators.Optional(TypeValidator(str, allow_none=True), None),
    'quantity': validators.Optional(str, None),
    'extraction_method': validators.Optional(str, None),
    'comment': validators.Optional(TypeValidator(str, allow_none=True), None),
}

ORDER_SCHEMES = {
    OrderType.EXTERNAL: Scheme({
        **BASE_PROJECT,
        'samples': ListValidator(EXTERNAL_SAMPLE, min_items=1)
    }),
    OrderType.MIP: Scheme({
        **BASE_PROJECT,
        'samples': ListValidator(MIP_SAMPLE, min_items=1)
    }),
    OrderType.BALSAMIC: Scheme({
        **BASE_PROJECT,
        'samples': ListValidator(BALSAMIC_SAMPLE, min_items=1),
    }),
    OrderType.MIP_BALSAMIC: Scheme({
        **BASE_PROJECT,
        'samples': ListValidator(MIP_BALSAMIC_SAMPLE, min_items=1),
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

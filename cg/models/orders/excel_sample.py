from pydantic import AfterValidator, BeforeValidator, Field
from typing_extensions import Annotated

from cg.models.orders.constants import ExcelSampleAliases
from cg.models.orders.sample_base import OrderSample
from cg.models.orders.validators.excel_sample_validators import (
    convert_sex,
    convert_to_date,
    convert_to_lower,
    convert_to_priority,
    numeric_value,
    parse_panels,
    replace_spaces_with_underscores,
    validate_data_analysis,
    validate_parent,
    validate_source,
)


class ExcelSample(OrderSample):
    age_at_sampling: str = Field(None, alias=ExcelSampleAliases.AGE_AT_SAMPLING)
    application: str = Field(..., alias=ExcelSampleAliases.APPLICATION)
    capture_kit: str = Field(None, alias=ExcelSampleAliases.CAPTURE_KIT)
    cohorts: list[str] = Field(None, alias=ExcelSampleAliases.COHORTS)
    collection_date: Annotated[str, AfterValidator(convert_to_date)] = Field(
        None, alias=ExcelSampleAliases.COLLECTION_DATE
    )
    comment: str = Field(None, alias=ExcelSampleAliases.COMMENT)
    concentration: Annotated[str, AfterValidator(numeric_value)] = Field(
        None, alias=ExcelSampleAliases.CONCENTRATION
    )
    concentration_ng_ul: str = Field(None, alias=ExcelSampleAliases.CONCENTRATION_NG_UL)
    concentration_sample: Annotated[str, AfterValidator(numeric_value)] = Field(
        None, alias=ExcelSampleAliases.CONCENTRATION_SAMPLE
    )
    container: str = Field(None, alias=ExcelSampleAliases.CONTAINER)
    container_name: str = Field(None, alias=ExcelSampleAliases.CONTAINER_NAME)
    control: str = Field(None, alias=ExcelSampleAliases.CONTROL)
    custom_index: str = Field(None, alias=ExcelSampleAliases.CUSTOM_INDEX)
    customer: str = Field(..., alias=ExcelSampleAliases.CUSTOMER)
    data_analysis: Annotated[str, AfterValidator(validate_data_analysis)] = Field(
        "MIP DNA", alias=ExcelSampleAliases.DATA_ANALYSIS
    )
    data_delivery: Annotated[str, AfterValidator(convert_to_lower)] = Field(
        None, alias=ExcelSampleAliases.DATA_DELIVERY
    )
    elution_buffer: str = Field(None, alias=ExcelSampleAliases.ELUTION_BUFFER)
    extraction_method: str = Field(None, alias=ExcelSampleAliases.EXTRACTION_METHOD)
    family_name: str = Field(None, alias=ExcelSampleAliases.FAMILY_NAME)
    father: Annotated[str, AfterValidator(validate_parent)] = Field(
        None, alias=ExcelSampleAliases.FATHER
    )
    formalin_fixation_time: str = Field(None, alias=ExcelSampleAliases.FORMALIN_FIXATION_TIME)
    index: str = Field(None, alias=ExcelSampleAliases.INDEX)
    index_number: Annotated[str, AfterValidator(numeric_value)] = Field(
        None, alias=ExcelSampleAliases.INDEX_NUMBER
    )
    lab_code: str = Field(None, alias=ExcelSampleAliases.LAB_CODE)
    mother: Annotated[str, AfterValidator(validate_parent)] = Field(
        None, alias=ExcelSampleAliases.MOTHER
    )
    name: str = Field(..., alias=ExcelSampleAliases.NAME)
    organism: str = Field(None, alias=ExcelSampleAliases.ORGANISM)
    organism_other: str = Field(None, alias=ExcelSampleAliases.ORGANISM_OTHER)
    original_lab: str = Field(None, alias=ExcelSampleAliases.ORIGINAL_LAB)
    original_lab_address: str = Field(None, alias=ExcelSampleAliases.ORIGINAL_LAB_ADDRESS)
    panels: Annotated[list[str] | None, BeforeValidator(parse_panels)] = Field(
        None, alias=ExcelSampleAliases.PANELS
    )
    pool: str = Field(None, alias=ExcelSampleAliases.POOL)
    post_formalin_fixation_time: str = Field(
        None, alias=ExcelSampleAliases.POST_FORMALIN_FIXATION_TIME
    )
    pre_processing_method: str = Field(None, alias=ExcelSampleAliases.PRE_PROCESSING_METHOD)
    primer: str = Field(None, alias=ExcelSampleAliases.PRIMER)
    priority: Annotated[
        str,
        AfterValidator(convert_to_lower),
        AfterValidator(convert_to_priority),
        AfterValidator(replace_spaces_with_underscores),
    ] = Field(None, alias=ExcelSampleAliases.PRIORITY)
    quantity: Annotated[str, AfterValidator(numeric_value)] = Field(
        None, alias=ExcelSampleAliases.QUANTITY
    )
    reagent_label: str = Field(None, alias=ExcelSampleAliases.REAGENT_LABEL)
    reference_genome: str = Field(None, alias=ExcelSampleAliases.REFERENCE_GENOME)
    region: str = Field(None, alias=ExcelSampleAliases.REGION)
    region_code: str = Field(None, alias=ExcelSampleAliases.REGION_CODE)
    require_qc_ok: bool = Field(None, alias=ExcelSampleAliases.REQUIRE_QC_OK)
    rml_plate_name: str = Field(None, alias=ExcelSampleAliases.RML_PLATE_NAME)
    selection_criteria: str = Field(None, alias=ExcelSampleAliases.SELECTION_CRITERIA)
    sex: Annotated[str, AfterValidator(convert_sex)] = Field(None, alias=ExcelSampleAliases.SEX)
    source: Annotated[str, AfterValidator(validate_source)] = Field(
        None, alias=ExcelSampleAliases.SOURCE
    )
    status: Annotated[str, AfterValidator(convert_to_lower)] = Field(
        None, alias=ExcelSampleAliases.STATUS
    )
    subject_id: str = Field(None, alias=ExcelSampleAliases.SUBJECT_ID)
    synopsis: str = Field(None, alias=ExcelSampleAliases.SYNOPSIS)
    tissue_block_size: str = Field(None, alias=ExcelSampleAliases.TISSUE_BLOCK_SIZE)
    tumour: bool = Field(None, alias=ExcelSampleAliases.TUMOUR)
    tumour_purity: str = Field(None, alias=ExcelSampleAliases.TUMOUR_PURITY)
    volume: Annotated[str, AfterValidator(numeric_value)] = Field(
        None, alias=ExcelSampleAliases.VOLUME
    )
    well_position: str = Field(None, alias=ExcelSampleAliases.WELL_POSITION)
    well_position_rml: str = Field(None, alias=ExcelSampleAliases.WELL_POSITION_RML)

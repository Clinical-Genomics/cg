from typing import List, Optional

from cg.models.orders.sample_base import OrderSample
from cg.models.orders.validators.excel_sample_validators import (
    convert_sex,
    convert_to_date,
    convert_to_lower,
    convert_to_priority,
    numeric_value,
    parse_panels,
    validate_data_analysis,
    validate_parent,
    validate_source,
    replace_spaces_with_underscores,
)
from pydantic import AfterValidator, BeforeValidator, Field
from typing_extensions import Annotated


class ExcelSample(OrderSample):
    age_at_sampling: str = Field(None, alias="UDF/age_at_sampling")
    application: str = Field(..., alias="UDF/Sequencing Analysis")
    capture_kit: str = Field(None, alias="UDF/Capture Library version")
    cohorts: List[str] = Field(None, alias="UDF/cohorts")
    collection_date: Annotated[str, AfterValidator(convert_to_date)] = Field(
        None, alias="UDF/Collection Date"
    )
    comment: str = Field(None, alias="UDF/Comment")
    concentration: Annotated[str, AfterValidator(numeric_value)] = Field(
        None, alias="UDF/Concentration (nM)"
    )
    concentration_sample: Annotated[str, AfterValidator(numeric_value)] = Field(
        None, alias="UDF/Sample Conc."
    )
    container: str = Field(None, alias="Container/Type")
    container_name: str = Field(None, alias="Container/Name")
    control: str = Field(None, alias="UDF/Control")
    custom_index: str = Field(None, alias="UDF/Custom index")
    customer: str = Field(..., alias="UDF/customer")
    data_analysis: Annotated[str, AfterValidator(validate_data_analysis)] = Field(
        "MIP DNA", alias="UDF/Data Analysis"
    )
    data_delivery: Annotated[str, AfterValidator(convert_to_lower)] = Field(
        None, alias="UDF/Data Delivery"
    )
    elution_buffer: str = Field(None, alias="UDF/Sample Buffer")
    extraction_method: str = Field(None, alias="UDF/Extraction method")
    family_name: str = Field(None, alias="UDF/familyID")
    father: Annotated[str, AfterValidator(validate_parent)] = Field(None, alias="UDF/fatherID")
    formalin_fixation_time: str = Field(None, alias="UDF/Formalin Fixation Time")
    index: str = Field(None, alias="UDF/Index type")
    index_number: Annotated[str, AfterValidator(numeric_value)] = Field(
        None, alias="UDF/Index number"
    )
    lab_code: str = Field(None, alias="UDF/Lab Code")
    mother: Annotated[str, AfterValidator(validate_parent)] = Field(None, alias="UDF/motherID")
    name: str = Field(..., alias="Sample/Name")
    organism: str = Field(None, alias="UDF/Strain")
    organism_other: str = Field(None, alias="UDF/Other species")
    original_lab: str = Field(None, alias="UDF/Original Lab")
    original_lab_address: str = Field(None, alias="UDF/Original Lab Address")
    panels: Annotated[Optional[List[str]], BeforeValidator(parse_panels)] = Field(
        None, alias="UDF/Gene List"
    )
    pool: str = Field(None, alias="UDF/pool name")
    post_formalin_fixation_time: str = Field(None, alias="UDF/Post Formalin Fixation Time")
    pre_processing_method: str = Field(None, alias="UDF/Pre Processing Method")
    primer: str = Field(None, alias="UDF/Primer")
    priority: Annotated[
        str,
        AfterValidator(convert_to_lower),
        AfterValidator(convert_to_priority),
        AfterValidator(replace_spaces_with_underscores),
    ] = Field(None, alias="UDF/priority")
    quantity: Annotated[str, AfterValidator(numeric_value)] = Field(None, alias="UDF/Quantity")
    reagent_label: str = Field(None, alias="Sample/Reagent Label")
    reference_genome: str = Field(None, alias="UDF/Reference Genome Microbial")
    region: str = Field(None, alias="UDF/Region")
    region_code: str = Field(None, alias="UDF/Region Code")
    require_qc_ok: bool = Field(None, alias="UDF/Process only if QC OK")
    rml_plate_name: str = Field(None, alias="UDF/RML plate name")
    selection_criteria: str = Field(None, alias="UDF/Selection Criteria")
    sex: Annotated[str, AfterValidator(convert_sex)] = Field(None, alias="UDF/Gender")
    source: Annotated[str, AfterValidator(validate_source)] = Field(None, alias="UDF/Source")
    status: Annotated[str, AfterValidator(convert_to_lower)] = Field(None, alias="UDF/Status")
    subject_id: str = Field(None, alias="UDF/subjectID")
    synopsis: str = Field(None, alias="UDF/synopsis")
    tissue_block_size: str = Field(None, alias="UDF/Tissue Block Size")
    tumour: bool = Field(None, alias="UDF/tumor")
    tumour_purity: str = Field(None, alias="UDF/tumour purity")
    volume: Annotated[str, AfterValidator(numeric_value)] = Field(None, alias="UDF/Volume (uL)")
    well_position: str = Field(None, alias="Sample/Well Location")
    well_position_rml: str = Field(None, alias="UDF/RML well position")

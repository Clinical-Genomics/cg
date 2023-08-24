from typing import List, Optional

from cg.constants.orderforms import REV_SEX_MAP, SOURCE_TYPES
from cg.models.orders.sample_base import OrderSample
from pydantic import AfterValidator, BeforeValidator, Field
from typing_extensions import Annotated


def parse_panels(panels: str):
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


def numeric_value(value: Optional[str]):
    if not value:
        return None
    str_value = value.rsplit(".0")[0]
    if str_value.replace(".", "").isnumeric():
        return str_value
    raise AttributeError(f"Order contains non-numeric value '{value}'")


def validate_parent(parent: str):
    return None if parent == "0.0" else parent


def validate_source(source: Optional[str]):
    if source not in SOURCE_TYPES:
        raise ValueError(f"'{source}' is not a valid source")
    return source


def convert_sex(sex: Optional[str]):
    if not sex:
        return None
    sex = sex.strip()
    return REV_SEX_MAP.get(sex, "unknown")


def convert_to_lower(value: Optional[str]):
    return value.lower()


def convert_to_priority(priority: Optional[str]):
    return "priority" if priority == "förtur" else priority


def convert_to_date(date: Optional[str]) -> Optional[str]:
    return None if not date else date[:10]


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

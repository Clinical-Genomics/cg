from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, validator, root_validator
from cg.constants import Pipeline
from cg.models.report.sample import SampleModel, ApplicationModel
from cg.models.report.validators import (
    validate_empty_field,
    validate_supported_pipeline,
    validate_list,
    validate_date,
)


class CustomerModel(BaseModel):
    """
    Customer model associated to the delivery report generated

    Attributes:
        name: customer name; source: statusDB/family/customer/name
        id: customer internal ID; source: statusDB/family/customer/internal_id
        invoice_address: customers invoice address; source: statusDB/family/customer/invoice_address
        scout_access: whether the customer has access to scout or not; source: statusDB/family/customer/scout_access
    """

    name: Optional[str]
    id: Optional[str]
    invoice_address: Optional[str]
    scout_access: Optional[bool]

    _values = validator("name", "id", "invoice_address", always=True, allow_reuse=True)(
        validate_empty_field
    )


class DataAnalysisModel(BaseModel):
    """
    Model that describes the pipeline attributes used for the data analysis

    Attributes:
        customer_pipeline: data analysis requested by the customer; source: StatusDB/family/data_analysis
        pipeline: actual pipeline used for analysis; source: statusDB/analysis/pipeline
        pipeline_version: pipeline version; source: statusDB/analysis/pipeline_version
        type: analysis type carried out; source: pipeline workflow
        genome_build: build version of the genome reference; source: pipeline workflow
        variant_callers: variant-calling filters
        panels: list of case specific panels; source: StatusDB/family/panels
    """

    customer_pipeline: Optional[Pipeline]
    pipeline: Optional[Pipeline]
    pipeline_version: Optional[str]
    type: Optional[str]
    genome_build: Optional[str]
    variant_callers: Union[None, List[str], str]
    panels: Union[None, List[str], str]

    _values = root_validator(pre=True, allow_reuse=True)(validate_supported_pipeline)
    _str_values = validator(
        "customer_pipeline",
        "pipeline",
        "pipeline_version",
        "type",
        "genome_build",
        always=True,
        allow_reuse=True,
    )(validate_empty_field)
    _list_values = validator("variant_callers", "panels", always=True, allow_reuse=True)(
        validate_list
    )


class CaseModel(BaseModel):
    """
    Defines the case/family model

    Attributes:
        name: case name; source: StatusDB/family/name
        samples: list of samples associated to a case/family
        data_analysis: pipeline attributes
        applications: case associated unique applications
    """

    name: Optional[str]
    samples: List[SampleModel]
    data_analysis: DataAnalysisModel
    applications: List[ApplicationModel]

    _name = validator("name", always=True, allow_reuse=True)(validate_empty_field)


class ReportModel(BaseModel):
    """
    Model that defines the report attributes to render

    Attributes:
        customer: customer attributes
        version: delivery report version; source: StatusDB/analysis/family/analyses(/index)
        date: report generation date; source: CG runtime
        case: case attributes
        accredited: whether the report is accredited or not; source: all(StatusDB/application/accredited)
    """

    customer: CustomerModel
    version: Union[None, int, str]
    date: Union[None, datetime, str]
    case: CaseModel
    accredited: Optional[bool]

    _version = validator("version", always=True, allow_reuse=True)(validate_empty_field)
    _date = validator("date", always=True, allow_reuse=True)(validate_date)

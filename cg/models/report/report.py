from datetime import datetime
from typing import List, Optional, Union

from pydantic.v1 import BaseModel, validator, root_validator
from cg.constants import Pipeline, DataDelivery
from cg.models.report.sample import SampleModel, ApplicationModel
from cg.models.report.validators import (
    validate_empty_field,
    validate_supported_pipeline,
    validate_list,
    validate_date,
    validate_path,
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


class ScoutReportFiles(BaseModel):
    """
    Model that describes the files uploaded to Scout and delivered to the customer

    Attributes:
        snv_vcf: SNV VCF file uploaded to Scout; source: HK
        snv_research_vcf: SNV research VCF file uploaded to Scout; source: HK
        sv_vcf: SV VCF file uploaded to Scout; source: HK
        sv_research_vcf: SV research VCF file uploaded to Scout; source: HK
        vcf_str: Short Tandem Repeat variants file (MIP-DNA specific); source: HK
        smn_tsv: SMN gene variants file (MIP-DNA specific); source: HK
    """

    snv_vcf: Optional[str]
    snv_research_vcf: Optional[str]
    sv_vcf: Optional[str]
    sv_research_vcf: Optional[str]
    vcf_str: Optional[str]
    smn_tsv: Optional[str]

    _str_values = validator(
        "snv_vcf",
        "snv_research_vcf",
        "sv_vcf",
        "sv_research_vcf",
        "vcf_str",
        "smn_tsv",
        always=True,
        allow_reuse=True,
    )(validate_path)


class DataAnalysisModel(BaseModel):
    """
    Model that describes the pipeline attributes used for the data analysis

    Attributes:
        customer_pipeline: data analysis requested by the customer; source: StatusDB/family/data_analysis
        data_delivery: data delivery requested by the customer; source: StatusDB/family/data_delivery
        pipeline: actual pipeline used for analysis; source: statusDB/analysis/pipeline
        pipeline_version: pipeline version; source: statusDB/analysis/pipeline_version
        type: analysis type carried out; source: pipeline workflow
        genome_build: build version of the genome reference; source: pipeline workflow
        variant_callers: variant-calling filters; source: pipeline workflow
        panels: list of case specific panels; source: StatusDB/family/panels
        scout_files: list of file names uploaded to Scout
    """

    customer_pipeline: Optional[Pipeline]
    data_delivery: Optional[DataDelivery]
    pipeline: Optional[Pipeline]
    pipeline_version: Optional[str]
    type: Optional[str]
    genome_build: Optional[str]
    variant_callers: Union[None, List[str], str]
    panels: Union[None, List[str], str]
    scout_files: ScoutReportFiles

    _values = root_validator(pre=True, allow_reuse=True)(validate_supported_pipeline)
    _str_values = validator(
        "customer_pipeline",
        "data_delivery",
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
        id: case ID; source: StatusDB/family/internal_id
        samples: list of samples associated to a case/family
        data_analysis: pipeline attributes
        applications: case associated unique applications
    """

    name: Optional[str]
    id: Optional[str]
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

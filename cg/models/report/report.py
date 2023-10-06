from typing import List, Optional

from pydantic import BaseModel, BeforeValidator, model_validator
from typing_extensions import Annotated

from cg.models.report.sample import SampleModel, ApplicationModel
from cg.models.report.validators import (
    validate_date,
    validate_empty_field,
    validate_list,
    validate_path,
    validate_supported_pipeline,
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

    name: Annotated[str, BeforeValidator(validate_empty_field)]
    id: Annotated[str, BeforeValidator(validate_empty_field)]
    invoice_address: Annotated[str, BeforeValidator(validate_empty_field)]
    scout_access: Optional[bool] = None


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

    snv_vcf: Annotated[str, BeforeValidator(validate_path)]
    snv_research_vcf: Annotated[str, BeforeValidator(validate_path)]
    sv_vcf: Annotated[str, BeforeValidator(validate_path)]
    sv_research_vcf: Annotated[str, BeforeValidator(validate_path)]
    vcf_str: Annotated[str, BeforeValidator(validate_path)]
    smn_tsv: Annotated[str, BeforeValidator(validate_path)]


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

    customer_pipeline: Annotated[str, BeforeValidator(validate_empty_field)]
    data_delivery: Annotated[str, BeforeValidator(validate_empty_field)]
    pipeline: Annotated[str, BeforeValidator(validate_empty_field)]
    pipeline_version: Annotated[str, BeforeValidator(validate_empty_field)]
    type: Annotated[str, BeforeValidator(validate_empty_field)]
    genome_build: Annotated[str, BeforeValidator(validate_empty_field)]
    variant_callers: Annotated[str, BeforeValidator(validate_list)]
    panels: Annotated[str, BeforeValidator(validate_list)]
    scout_files: ScoutReportFiles

    _values = model_validator(mode="after")(validate_supported_pipeline)


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

    name: Annotated[str, BeforeValidator(validate_empty_field)]
    id: Annotated[str, BeforeValidator(validate_empty_field)]
    samples: List[SampleModel]
    data_analysis: DataAnalysisModel
    applications: List[ApplicationModel]


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
    version: Annotated[str, BeforeValidator(validate_empty_field)]
    date: Annotated[str, BeforeValidator(validate_date)]
    case: CaseModel
    accredited: Optional[bool] = None

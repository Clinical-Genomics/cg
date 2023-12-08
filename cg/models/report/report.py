import logging

from pydantic import BaseModel, BeforeValidator, model_validator
from typing_extensions import Annotated

from cg.constants import NA_FIELD, REPORT_SUPPORTED_PIPELINES
from cg.models.report.sample import ApplicationModel, SampleModel
from cg.models.report.validators import (
    get_analysis_type_as_string,
    get_date_as_string,
    get_list_as_string,
    get_path_as_string,
    get_report_string,
)

LOG = logging.getLogger(__name__)


class CustomerModel(BaseModel):
    """
    Customer model associated to the delivery report generated

    Attributes:
        name: customer name; source: statusDB/family/customer/name
        id: customer internal ID; source: statusDB/family/customer/internal_id
        invoice_address: customers invoice address; source: statusDB/family/customer/invoice_address
        scout_access: whether the customer has access to scout or not; source: statusDB/family/customer/scout_access
    """

    name: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    id: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    invoice_address: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    scout_access: bool | None = None


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
        vcf_fusion: Converted RNA fusion file to SV VCF (RNAfusion specific); source: HK
    """

    snv_vcf: Annotated[str, BeforeValidator(get_path_as_string)] = NA_FIELD
    snv_research_vcf: Annotated[str, BeforeValidator(get_path_as_string)] = NA_FIELD
    sv_vcf: Annotated[str, BeforeValidator(get_path_as_string)] = NA_FIELD
    sv_research_vcf: Annotated[str, BeforeValidator(get_path_as_string)] = NA_FIELD
    vcf_str: Annotated[str, BeforeValidator(get_path_as_string)] = NA_FIELD
    smn_tsv: Annotated[str, BeforeValidator(get_path_as_string)] = NA_FIELD
    vcf_fusion: Annotated[str, BeforeValidator(get_path_as_string)] = NA_FIELD


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

    customer_pipeline: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    data_delivery: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    pipeline: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    pipeline_version: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    type: Annotated[str, BeforeValidator(get_analysis_type_as_string)] = NA_FIELD
    genome_build: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    variant_callers: Annotated[str, BeforeValidator(get_list_as_string)] = NA_FIELD
    panels: Annotated[str, BeforeValidator(get_list_as_string)] = NA_FIELD
    scout_files: ScoutReportFiles

    @model_validator(mode="after")
    def check_supported_pipeline(self) -> "DataAnalysisModel":
        """Check if the report generation supports a specific pipeline and analysis type."""
        if self.pipeline != self.customer_pipeline:
            LOG.error(
                f"The analysis requested by the customer ({self.customer_pipeline}) does not match the one "
                f"executed ({self.pipeline})"
            )
            raise ValueError
        if self.pipeline not in REPORT_SUPPORTED_PIPELINES:
            LOG.error(f"The pipeline {self.pipeline} does not support delivery report generation")
            raise ValueError
        return self


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

    name: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    id: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    samples: list[SampleModel]
    data_analysis: DataAnalysisModel
    applications: list[ApplicationModel]


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
    version: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    date: Annotated[str, BeforeValidator(get_date_as_string)] = NA_FIELD
    case: CaseModel
    accredited: bool | None = None

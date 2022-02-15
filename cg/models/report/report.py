import logging
from datetime import datetime
from typing import List

from cg.constants.orderforms import CASE_PROJECT_TYPES
from pydantic import BaseModel
from cg.models.report.sample import SampleModel

LOG = logging.getLogger(__name__)


class CustomerModel(BaseModel):
    """
    Customer model associated to the delivery report generated

    Attributes:
        name: customer name
        id: customer internal ID
        invoice_address: customers invoice address
        scout_access: whether the customer has access to scout or not
    """

    name: str
    id: str
    invoice_address: str
    scout_access: bool


class CaseModel(BaseModel):
    """
    Defines the case/family model

    Attributes:
        id: case internal ID
        genome_build: build version of the genome reference
        pipeline: data analysis requested by the customer
        samples: list of samples associated to a case/family
    """

    id: str
    genome_build: str
    pipeline: CASE_PROJECT_TYPES
    samples: List[SampleModel]


class ReportModel(BaseModel):
    """
    Model that defines the report attributes to render

    Attributes:
        customer: customer attributes
        version: delivery report version
        accreditation: shows if the report is accredited or not
        date: report generation date
        case: case attributes
    """

    customer: CustomerModel
    version: str
    accreditation: bool
    date: datetime
    case: CaseModel

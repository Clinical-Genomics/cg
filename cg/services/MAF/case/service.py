from cg.constants import DataDelivery, Workflow, GenePanelMasterList, Priority
from cg.constants.constants import CustomerId
from cg.models.orders.sample_base import StatusEnum
from cg.store.models import CaseSample, Case, Sample, Order
from cg.store.store import Store


class MAFCaseService:
    """Service for creating MAF cases in the Status database for fastq orders."""

    def __init__(self, store: Store):
        self.status_db = store

    def create_maf_case(self, sample_obj: Sample, order: Order) -> None:
        """Add a MAF case to the Status database."""
        case: Case = self.status_db.add_case(
            data_analysis=Workflow(Workflow.MIP_DNA),
            data_delivery=DataDelivery(DataDelivery.NO_DELIVERY),
            name="_".join([sample_obj.name, "MAF"]),
            panels=[GenePanelMasterList.OMIM_AUTO],
            priority=Priority.research,
            ticket=sample_obj.original_ticket,
        )
        case.customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=CustomerId.CG_INTERNAL_CUSTOMER
        )
        relationship: CaseSample = self.status_db.relate_sample(
            case=case, sample=sample_obj, status=StatusEnum.unknown
        )
        order.cases.append(case)
        self.status_db.session.add_all([case, relationship])

    def does_maf_case_exist(self, sample_obj: Sample) -> bool:
        """Check if a MAF case already exists for a sample."""
        case: Case = self.status_db.get_case_by_name_and_customer(
            customer=self.status_db.get_customer_by_internal_id(),
            case_name="_".join([sample_obj.name, "MAF"]),
        )
        return bool(case)

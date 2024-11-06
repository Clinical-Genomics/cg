from cg.constants import DataDelivery, Workflow, GenePanelMasterList, Priority
from cg.constants.constants import CustomerId
from cg.models.orders.sample_base import StatusEnum
from cg.store.models import CaseSample, Case, Sample, Order
from cg.store.store import Store


class MAFCaseService:
    """Service for creating MAF cases in the Status database for fastq orders."""

    def __init__(self, store: Store):
        self.status_db = store

    def create_maf_cases(self) -> None:
        """Create MAF cases for all samples in an order."""
        samples: list[Sample] = self.status_db.get_samples_for_maf_cases()
        for sample in samples:
            if self._does_maf_case_exist(sample):
                continue
            self._create_maf_case(sample)

    def _create_maf_case(self, sample: Sample) -> None:
        """Add a MAF case to the Status database."""
        case: Case = self.status_db.add_case(
            data_analysis=Workflow(Workflow.MIP_DNA),
            data_delivery=DataDelivery(DataDelivery.NO_DELIVERY),
            name="_".join([sample.name, "MAF"]),
            panels=[GenePanelMasterList.OMIM_AUTO],
            priority=Priority.research,
            ticket=sample.original_ticket,
        )
        case.customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=CustomerId.CG_INTERNAL_CUSTOMER
        )
        relationship: CaseSample = self.status_db.relate_sample(
            case=case, sample=sample, status=StatusEnum.unknown
        )
        # order stuff needs to be fixed
        self.status_db.session.add_all([case, relationship])

    def _does_maf_case_exist(self, sample: Sample) -> bool:
        """Check if a MAF case already exists for a sample."""
        case: Case = self.status_db.get_case_by_name_and_customer(
            customer=sample.customer.internal_id,
            case_name="_".join([sample.name, "MAF"]),
        )
        return bool(case)

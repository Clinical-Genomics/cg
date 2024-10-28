import logging
from datetime import datetime

from cg.constants import Priority, Workflow
from cg.constants.constants import CaseActions, DataDelivery
from cg.constants.pedigree import Pedigree
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import Of1508Sample
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.submitters.order_submitter import StoreOrderService
from cg.store.models import (
    ApplicationVersion,
    Case,
    CaseSample,
    Customer,
    Order,
    Sample,
)
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class StoreCaseOrderService(StoreOrderService):
    """
    Service for storing generic orders in StatusDB and Lims.
    This class is used to store orders for the following workflows:
    - Balsamic
    - Balsamic QC
    - Balsamic UMI
    - MIP DNA
    - MIP RNA
    - Tomte
    """

    def __init__(
        self,
        status_db: Store,
        lims_service: OrderLimsService,
    ):
        self.status_db = status_db
        self.lims = lims_service

    def store_order(self, order: OrderIn) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        return self._process_case_samples(order=order)

    def _process_case_samples(self, order: OrderIn) -> dict:
        """Process samples to be analyzed."""
        project_data = lims_map = None

        # submit new samples to lims
        new_samples = [sample for sample in order.samples if sample.internal_id is None]
        if new_samples:
            project_data, lims_map = self.lims.process_lims(
                lims_order=order, new_samples=new_samples
            )

        status_data = self.order_to_status(order=order)
        samples = [sample for family in status_data["families"] for sample in family["samples"]]
        if lims_map:
            self._fill_in_sample_ids(samples=samples, lims_map=lims_map)

        new_cases: list[Case] = self.store_items_in_status(
            customer_id=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"] if project_data else datetime.now(),
            ticket_id=order.ticket,
            items=status_data["families"],
        )
        return {"project": project_data, "records": new_cases}

    @staticmethod
    def _group_cases(samples: list[Of1508Sample]) -> dict:
        """Group samples in cases."""
        cases = {}
        for sample in samples:
            case_id = sample.family_name
            if case_id not in cases:
                cases[case_id] = []
            cases[case_id].append(sample)
        return cases

    @staticmethod
    def _get_single_value(case_name, case_samples, value_key, value_default=None):
        values = set(getattr(sample, value_key) or value_default for sample in case_samples)
        if len(values) > 1:
            raise ValueError(f"different sample {value_key} values: {case_name} - {values}")
        single_value = values.pop()
        return single_value

    def order_to_status(self, order: OrderIn) -> dict:
        """Converts order input to status interface input for MIP-DNA, MIP-RNA and Balsamic."""
        status_data = {"customer": order.customer, "order": order.name, "families": []}
        cases = self._group_cases(order.samples)

        for case_name, case_samples in cases.items():
            case_internal_id: str = self._get_single_value(
                case_name, case_samples, "case_internal_id"
            )
            cohorts: set[str] = {
                cohort for sample in case_samples for cohort in sample.cohorts if cohort
            }
            data_analysis = self._get_single_value(case_name, case_samples, "data_analysis")
            data_delivery = self._get_single_value(case_name, case_samples, "data_delivery")

            panels: set[str] = set()
            if data_analysis in [Workflow.MIP_DNA, Workflow.TOMTE]:
                panels: set[str] = {
                    panel for sample in case_samples for panel in sample.panels if panel
                }

            priority = self._get_single_value(
                case_name, case_samples, "priority", Priority.standard.name
            )
            synopsis: str = self._get_single_value(case_name, case_samples, "synopsis")

            case = {
                "cohorts": list(cohorts),
                "data_analysis": data_analysis,
                "data_delivery": data_delivery,
                "internal_id": case_internal_id,
                "name": case_name,
                "panels": list(panels),
                "priority": priority,
                "samples": [
                    {
                        "age_at_sampling": sample.age_at_sampling,
                        "application": sample.application,
                        "capture_kit": sample.capture_kit,
                        "comment": sample.comment,
                        "control": sample.control,
                        "father": sample.father,
                        "internal_id": sample.internal_id,
                        "mother": sample.mother,
                        "name": sample.name,
                        "phenotype_groups": list(sample.phenotype_groups),
                        "phenotype_terms": list(sample.phenotype_terms),
                        "reference_genome": (
                            sample.reference_genome if hasattr(sample, "reference_genome") else None
                        ),
                        "sex": sample.sex,
                        "status": sample.status if hasattr(sample, "status") else None,
                        "subject_id": sample.subject_id,
                        "tumour": sample.tumour,
                    }
                    for sample in case_samples
                ],
                "synopsis": synopsis,
            }

            status_data["families"].append(case)
        return status_data

    def store_items_in_status(
        self, customer_id: str, order: str, ordered: datetime, ticket_id: str, items: list[dict]
    ) -> list[Case]:
        """Store cases, samples and their relationship in the Status database."""
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        new_cases: list[Case] = []
        status_db_order = Order(
            customer=customer,
            order_date=datetime.now(),
            ticket_id=int(ticket_id),
            workflow=Workflow(items[0]["data_analysis"]),
        )
        for case in items:
            status_db_case: Case = self.status_db.get_case_by_internal_id(
                internal_id=case["internal_id"]
            )
            if not status_db_case:
                new_case: Case = self._create_case(
                    case=case, customer_obj=customer, ticket=ticket_id
                )
                new_cases.append(new_case)
                self._update_case_panel(panels=case["panels"], case=new_case)
                status_db_case: Case = new_case
            else:
                self._append_ticket(ticket_id=ticket_id, case=status_db_case)
                self._update_action(action=CaseActions.ANALYZE, case=status_db_case)
                self._update_case_panel(panels=case["panels"], case=status_db_case)
            case_samples: dict[str, Sample] = {}
            status_db_order.cases.append(status_db_case)
            for sample in case["samples"]:
                existing_sample: Sample = self.status_db.get_sample_by_internal_id(
                    internal_id=sample["internal_id"]
                )
                if not existing_sample:
                    new_sample: Sample = self._create_sample(
                        case=case,
                        customer_obj=customer,
                        order=order,
                        ordered=ordered,
                        sample=sample,
                        ticket=ticket_id,
                    )
                    case_samples[sample["name"]] = new_sample
                else:
                    case_samples[sample["name"]] = existing_sample

            for sample in case["samples"]:
                sample_mother: Sample = case_samples.get(sample.get(Pedigree.MOTHER))
                sample_father: Sample = case_samples.get(sample.get(Pedigree.FATHER))
                with self.status_db.session.no_autoflush:
                    case_sample: CaseSample = self.status_db.get_case_sample_link(
                        case_internal_id=status_db_case.internal_id,
                        sample_internal_id=sample["internal_id"],
                    )
                if not case_sample:
                    case_sample: CaseSample = self._create_link(
                        case_obj=status_db_case,
                        family_samples=case_samples,
                        father_obj=sample_father,
                        mother_obj=sample_mother,
                        sample=sample,
                    )

                self._update_relationship(
                    father_obj=sample_father,
                    link_obj=case_sample,
                    mother_obj=sample_mother,
                    sample=sample,
                )
            self.status_db.session.add_all(new_cases)
            self.status_db.session.add(status_db_order)
            self.status_db.session.commit()
        return new_cases

    @staticmethod
    def _update_case_panel(panels: list[str], case: Case) -> None:
        """Update case panels."""
        case.panels = panels

    @staticmethod
    def _append_ticket(ticket_id: str, case: Case) -> None:
        """Add a ticket to the case."""
        case.tickets = f"{case.tickets},{ticket_id}"

    @staticmethod
    def _update_action(action: str, case: Case) -> None:
        """Update action of a case."""
        case.action = action

    @staticmethod
    def _update_relationship(father_obj, link_obj, mother_obj, sample):
        link_obj.status = sample["status"] or link_obj.status
        link_obj.mother = mother_obj or link_obj.mother
        link_obj.father = father_obj or link_obj.father

    def _create_link(self, case_obj, family_samples, father_obj, mother_obj, sample):
        link_obj = self.status_db.relate_sample(
            case=case_obj,
            sample=family_samples[sample["name"]],
            status=sample["status"],
            mother=mother_obj,
            father=father_obj,
        )
        self.status_db.session.add(link_obj)
        return link_obj

    def _create_sample(self, case, customer_obj, order, ordered, sample, ticket):
        sample_obj = self.status_db.add_sample(
            name=sample["name"],
            comment=sample["comment"],
            control=sample["control"],
            internal_id=sample["internal_id"],
            order=order,
            ordered=ordered,
            original_ticket=ticket,
            tumour=sample["tumour"],
            age_at_sampling=sample["age_at_sampling"],
            capture_kit=sample["capture_kit"],
            phenotype_groups=sample["phenotype_groups"],
            phenotype_terms=sample["phenotype_terms"],
            priority=case["priority"],
            reference_genome=sample["reference_genome"],
            sex=sample["sex"],
            subject_id=sample["subject_id"],
        )
        sample_obj.customer = customer_obj
        with self.status_db.session.no_autoflush:
            application_tag = sample["application"]
            sample_obj.application_version: ApplicationVersion = (
                self.status_db.get_current_application_version_by_tag(tag=application_tag)
            )
        self.status_db.session.add(sample_obj)
        return sample_obj

    def _create_case(self, case: dict, customer_obj: Customer, ticket: str):
        case_obj = self.status_db.add_case(
            cohorts=case["cohorts"],
            data_analysis=Workflow(case["data_analysis"]),
            data_delivery=DataDelivery(case["data_delivery"]),
            name=case["name"],
            priority=case["priority"],
            synopsis=case["synopsis"],
            ticket=ticket,
        )
        case_obj.customer = customer_obj
        return case_obj

    @staticmethod
    def _is_rerun_of_existing_case(sample: Of1508Sample) -> bool:
        return sample.case_internal_id is not None

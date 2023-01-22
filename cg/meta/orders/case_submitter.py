import datetime as dt
import logging
from typing import List, Set

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.constants.constants import CaseActions
from cg.exc import OrderError
from cg.meta.orders.lims import process_lims
from cg.meta.orders.submitter import Submitter
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import Of1508Sample, OrderInSample
from cg.store import models

from cg.constants import Priority

LOG = logging.getLogger(__name__)


class CaseSubmitter(Submitter):
    def validate_order(self, order: OrderIn) -> None:
        self._validate_samples_available_to_customer(
            samples=order.samples, customer_id=order.customer
        )
        self._validate_case_names_are_unique(samples=order.samples, customer_id=order.customer)
        self._validate_subject_sex(samples=order.samples, customer_id=order.customer)

    def _validate_subject_sex(self, samples: [Of1508Sample], customer_id: str):
        """Validate that sex is consistent with existing samples, skips samples of unknown sex

        Args:
            samples     (list[dict]):   Samples to validate
            customer_id (str):          Customer that the samples belong to
        Returns:
            Nothing
        """

        sample: Of1508Sample
        for sample in samples:
            subject_id: str = sample.subject_id
            if not subject_id:
                continue
            new_gender: str = sample.sex
            if new_gender == "unknown":
                continue
            existing_samples: [models.Sample] = self.status.samples_by_subject_id(
                customer_id=customer_id, subject_id=subject_id
            )
            existing_sample: models.Sample
            for existing_sample in existing_samples:
                previous_gender = existing_sample.sex
                if previous_gender == "unknown":
                    continue

                if previous_gender != new_gender:
                    raise OrderError(
                        f"Sample gender inconsistency for subject_id: {subject_id}: previous gender {previous_gender}, new gender {new_gender}"
                    )

    def _validate_samples_available_to_customer(
        self, samples: List[OrderInSample], customer_id: str
    ) -> None:
        """Validate that the customer have access to all samples"""
        sample: Of1508Sample
        for sample in samples:
            if not sample.internal_id:
                continue

            existing_sample: models.Sample = self.status.sample(sample.internal_id)
            data_customer: models.Customer = self.status.customer(customer_id)

            if existing_sample.customer not in data_customer.collaborators:
                raise OrderError(f"Sample not available: {sample.name}")

    def _validate_case_names_are_unique(
        self, samples: List[OrderInSample], customer_id: str
    ) -> None:
        """Validate that the names of all cases are unused for all samples"""
        customer_obj: models.Customer = self.status.customer(customer_id)

        sample: Of1508Sample
        for sample in samples:

            if self._is_rerun_of_existing_case(sample):
                continue

            if self.status.find_family(customer=customer_obj, name=sample.family_name):
                raise OrderError(f"Case name {sample.family_name} already in use")

    def submit_order(self, order: OrderIn) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        result = self._process_case_samples(order=order)
        for case_obj in result["records"]:
            LOG.info(f"{case_obj.name}: submit family samples")
            status_samples = [
                link_obj.sample
                for link_obj in case_obj.links
                if link_obj.sample.original_ticket == order.ticket
            ]
            self._add_missing_reads(status_samples)
        return result

    def _process_case_samples(self, order: OrderIn) -> dict:
        """Process samples to be analyzed."""
        project_data = lims_map = None

        # submit new samples to lims
        new_samples = [sample for sample in order.samples if sample.internal_id is None]
        if new_samples:
            project_data, lims_map = process_lims(
                lims_api=self.lims, lims_order=order, new_samples=new_samples
            )

        status_data = self.order_to_status(order=order)
        samples = [sample for family in status_data["families"] for sample in family["samples"]]
        if lims_map:
            self._fill_in_sample_ids(samples, lims_map)

        new_families = self.store_items_in_status(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"] if project_data else dt.datetime.now(),
            ticket=order.ticket,
            items=status_data["families"],
        )
        return {"project": project_data, "records": new_families}

    @staticmethod
    def _group_cases(samples: List[Of1508Sample]) -> dict:
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

    @staticmethod
    def order_to_status(order: OrderIn) -> dict:
        """Converts order input to status interface input for MIP-DNA, MIP-RNA and Balsamic."""
        status_data = {"customer": order.customer, "order": order.name, "families": []}
        cases = CaseSubmitter._group_cases(order.samples)

        for case_name, case_samples in cases.items():

            case_internal_id: str = CaseSubmitter._get_single_value(
                case_name, case_samples, "case_internal_id"
            )
            cohorts: Set[str] = {
                cohort for sample in case_samples for cohort in sample.cohorts if cohort
            }
            data_analysis = CaseSubmitter._get_single_value(
                case_name, case_samples, "data_analysis"
            )
            data_delivery = CaseSubmitter._get_single_value(
                case_name, case_samples, "data_delivery"
            )

            panels: Set[str] = set()
            if data_analysis == Pipeline.MIP_DNA:
                panels: Set[str] = {
                    panel for sample in case_samples for panel in sample.panels if panel
                }

            priority = CaseSubmitter._get_single_value(
                case_name, case_samples, "priority", Priority.standard.name
            )
            synopsis: str = CaseSubmitter._get_single_value(case_name, case_samples, "synopsis")

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
                        "reference_genome": sample.reference_genome
                        if hasattr(sample, "reference_genome")
                        else None,
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
        self, customer: str, order: str, ordered: dt.datetime, ticket: str, items: List[dict]
    ) -> List[models.Family]:
        """Store cases and samples in the status database."""

        customer_obj = self.status.customer(customer)
        new_families = []
        for case in items:
            case_obj = self.status.family(case["internal_id"])
            if not case_obj:
                case_obj = self._create_case(case, customer_obj, ticket)
                new_families.append(case_obj)
            else:
                self._append_ticket(ticket=ticket, case=case_obj)
                self._update_action(action=CaseActions.ANALYZE, case=case_obj)

            self._update_case(case, case_obj)

            family_samples = {}
            for sample in case["samples"]:
                sample_obj = self.status.sample(sample["internal_id"])
                if not sample_obj:
                    sample_obj = self._create_sample(
                        case, customer_obj, order, ordered, sample, ticket
                    )

                family_samples[sample["name"]] = sample_obj

            for sample in case["samples"]:
                mother_obj = family_samples.get(sample.get("mother"))
                father_obj = family_samples.get(sample.get("father"))
                with self.status.session.no_autoflush:
                    link_obj = self.status.link(case_obj.internal_id, sample["internal_id"])
                if not link_obj:
                    link_obj = self._create_link(
                        case_obj, family_samples, father_obj, mother_obj, sample
                    )

                self._update_relationship(father_obj, link_obj, mother_obj, sample)

            self.status.add_commit(new_families)
        return new_families

    @staticmethod
    def _update_case(case, case_obj):
        case_obj.panels = case["panels"]

    @staticmethod
    def _append_ticket(ticket: str, case: models.Family) -> None:
        """Add a ticket to the case."""
        case.tickets = f"{case.tickets},{ticket}"

    @staticmethod
    def _update_action(action: str, case: models.Family) -> None:
        """Update action of a case."""
        case.action = action

    @staticmethod
    def _update_relationship(father_obj, link_obj, mother_obj, sample):
        link_obj.status = sample["status"] or link_obj.status
        link_obj.mother = mother_obj or link_obj.mother
        link_obj.father = father_obj or link_obj.father

    def _create_link(self, case_obj, family_samples, father_obj, mother_obj, sample):
        link_obj = self.status.relate_sample(
            family=case_obj,
            sample=family_samples[sample["name"]],
            status=sample["status"],
            mother=mother_obj,
            father=father_obj,
        )
        self.status.add(link_obj)
        return link_obj

    def _create_sample(self, case, customer_obj, order, ordered, sample, ticket):
        sample_obj = self.status.add_sample(
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
        with self.status.session.no_autoflush:
            application_tag = sample["application"]
            sample_obj.application_version = self.status.current_application_version(
                application_tag
            )
        self.status.add(sample_obj)
        new_delivery = self.status.add_delivery(destination="caesar", sample=sample_obj)
        self.status.add(new_delivery)
        return sample_obj

    def _create_case(self, case: dict, customer_obj: models.Customer, ticket: str):
        case_obj = self.status.add_case(
            cohorts=case["cohorts"],
            data_analysis=Pipeline(case["data_analysis"]),
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

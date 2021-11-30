import logging
from typing import List, Set

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.exc import OrderError
from cg.meta.orders.lims import process_lims
from cg.meta.orders.submitter import Submitter
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import Of1508Sample, OrderInSample
from cg.store import models

import datetime as dt

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

            if existing_sample.customer.customer_group_id != data_customer.customer_group_id:
                raise OrderError(f"Sample not available: {sample.name}")

    def _validate_case_names_are_unique(
        self, samples: List[OrderInSample], customer_id: str
    ) -> None:
        """Validate that the names of all cases are unused for all samples"""
        customer_obj: models.Customer = self.status.customer(customer_id)

        sample: Of1508Sample
        for sample in samples:

            if self._rerun_of_existing_case(sample):
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
                if link_obj.sample.ticket_number == order.ticket
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

        status_data = self.cases_to_status(order=order)
        samples = [sample for family in status_data["families"] for sample in family["samples"]]
        if lims_map:
            self._fill_in_sample_ids(samples, lims_map)

        new_families = self.store_cases(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"] if project_data else dt.datetime.now(),
            ticket=order.ticket,
            cases=status_data["families"],
        )
        return {"project": project_data, "records": new_families}

    @staticmethod
    def group_cases(samples: List[Of1508Sample]) -> dict:
        """Group samples in cases."""
        cases = {}
        for sample in samples:
            case_id = sample.family_name
            if case_id not in cases:
                cases[case_id] = []
            cases[case_id].append(sample)
        return cases

    @classmethod
    def get_single_value(cls, case_name, case_samples, value_key, value_default=None):
        values = set(getattr(sample, value_key) or value_default for sample in case_samples)
        if len(values) > 1:
            raise ValueError(f"different sample {value_key} values: {case_name} - {values}")
        single_value = values.pop()
        return single_value

    @classmethod
    def cases_to_status(cls, order: OrderIn) -> dict:
        """Convert order input to status interface input."""
        status_data = {"customer": order.customer, "order": order.name, "families": []}
        cases = cls.group_cases(order.samples)

        for case_name, case_samples in cases.items():

            cohorts: Set[str] = {
                cohort for sample in case_samples for cohort in sample.cohorts if cohort
            }
            synopsis: str = ", ".join(set(sample.synopsis or "" for sample in case_samples))

            case_internal_id: str = cls.get_single_value(
                case_name, case_samples, "case_internal_id"
            )
            data_analysis = cls.get_single_value(case_name, case_samples, "data_analysis")
            data_delivery = cls.get_single_value(case_name, case_samples, "data_delivery")
            priority = cls.get_single_value(case_name, case_samples, "priority", "standard")

            # TODO: move to MIP-DNA submitter
            panels: Set[str] = set()
            if data_analysis == Pipeline.MIP_DNA:
                panels: Set[str] = {
                    panel for sample in case_samples for panel in sample.panels if panel
                }

            case = {
                "cohorts": cohorts,
                "data_analysis": data_analysis,
                "data_delivery": data_delivery,
                "name": case_name,
                "internal_id": case_internal_id,
                "priority": priority,
                "panels": list(panels),  # TODO: move to MIP-DNA submitter
                "samples": [
                    {
                        "age_at_sampling": sample.age_at_sampling,
                        "application": sample.application,
                        "capture_kit": sample.capture_kit,
                        "comment": sample.comment,
                        "father": sample.father,
                        "internal_id": sample.internal_id,
                        "mother": sample.mother,
                        "name": sample.name,
                        "phenotype_groups": list(sample.phenotype_groups),
                        "phenotype_terms": list(sample.phenotype_terms),
                        "sex": sample.sex,
                        "status": sample.status
                        if hasattr(sample, "status")
                        else None,  # TODO: move to RNA submitter
                        "subject_id": sample.subject_id,
                        "time_point": sample.time_point
                        if hasattr(sample, "time_point")
                        else None,  # TODO: move to RNA submitter
                        "tumour": sample.tumour,
                    }
                    for sample in case_samples
                ],
                "synopsis": synopsis,
            }

            status_data["families"].append(case)
        return status_data

    def store_cases(
        self, customer: str, order: str, ordered: dt.datetime, ticket: int, cases: List[dict]
    ) -> List[models.Family]:
        """Store cases and samples in the status database."""

        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"Unknown customer: {customer}")
        new_families = []
        for case in cases:
            case_obj = self.status.family(case["internal_id"])
            if case_obj:
                case_obj.panels = case["panels"]
            else:
                case_obj = self.status.add_case(
                    cohorts=case["cohorts"],
                    data_analysis=Pipeline(case["data_analysis"]),
                    data_delivery=DataDelivery(case["data_delivery"]),
                    name=case["name"],
                    panels=case["panels"],
                    priority=case["priority"],
                    synopsis=case["synopsis"],
                )
                case_obj.customer = customer_obj
                new_families.append(case_obj)

            family_samples = {}
            for sample in case["samples"]:
                sample_obj = self.status.sample(sample["internal_id"])
                if sample_obj:
                    family_samples[sample["name"]] = sample_obj
                else:
                    new_sample = self.status.add_sample(
                        age_at_sampling=sample["age_at_sampling"],
                        capture_kit=sample["capture_kit"],
                        comment=sample["comment"],
                        internal_id=sample["internal_id"],
                        name=sample["name"],
                        order=order,
                        ordered=ordered,
                        phenotype_groups=sample["phenotype_groups"],
                        phenotype_terms=sample["phenotype_terms"],
                        priority=case["priority"],
                        sex=sample["sex"],
                        subject_id=sample["subject_id"],
                        ticket=ticket,
                        time_point=sample["time_point"],
                        tumour=sample["tumour"],
                    )
                    new_sample.customer = customer_obj
                    with self.status.session.no_autoflush:
                        application_tag = sample["application"]
                        new_sample.application_version = self.status.current_application_version(
                            application_tag
                        )
                    if new_sample.application_version is None:
                        raise OrderError(f"Invalid application: {sample['application']}")

                    family_samples[new_sample.name] = new_sample
                    self.status.add(new_sample)
                    new_delivery = self.status.add_delivery(destination="caesar", sample=new_sample)
                    self.status.add(new_delivery)

            for sample in case["samples"]:
                mother_obj = family_samples.get(sample["mother"]) if sample.get("mother") else None
                father_obj = family_samples.get(sample["father"]) if sample.get("father") else None
                with self.status.session.no_autoflush:
                    link_obj = self.status.link(case_obj.internal_id, sample["internal_id"])
                if link_obj:
                    link_obj.status = sample["status"] or link_obj.status
                    link_obj.mother = mother_obj or link_obj.mother
                    link_obj.father = father_obj or link_obj.father
                else:
                    new_link = self.status.relate_sample(
                        family=case_obj,
                        sample=family_samples[sample["name"]],
                        status=sample["status"],
                        mother=mother_obj,
                        father=father_obj,
                    )
                    self.status.add(new_link)
            self.status.add_commit(new_families)
        return new_families

    @staticmethod
    def _rerun_of_existing_case(sample: Of1508Sample) -> bool:
        return sample.case_internal_id is not None

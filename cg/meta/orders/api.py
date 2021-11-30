"""Unified interface to handle sample submissions.

This interface will update information in Status and/or LIMS as required.

The normal entry for information is through the REST API which will pass a JSON
document with all information about samples in the submission. The input will
be validated and if passing all checks be accepted as new samples.
"""
import datetime as dt
import logging
import typing
from typing import List, Optional

from cg.apps.lims import LimsAPI
from cg.apps.osticket import OsTicket
from cg.constants import DataDelivery, Pipeline
from cg.exc import OrderError
from cg.models.orders.order import OrderIn, OrderType
from cg.store import Store, models

from .lims import process_lims
from .status import StatusHandler
from .ticket_handler import TicketHandler
from ...models.orders.samples import OrderInSample, Of1508Sample, MicrobialSample

LOG = logging.getLogger(__name__)


class OrdersAPI(StatusHandler):
    """Orders API for accepting new samples into the system."""

    def __init__(self, lims: LimsAPI, status: Store, osticket: OsTicket):
        super().__init__()
        self.lims = lims
        self.status = status
        self.ticket_handler: TicketHandler = TicketHandler(osticket_api=osticket, status_db=status)

    def submit(self, project: OrderType, order_in: OrderIn, user_name: str, user_mail: str) -> dict:
        """Submit a batch of samples.

        Main entry point for the class towards interfaces that implements it.
        """
        self.validate_order(order_in, project)

        # detect manual ticket assignment
        ticket_number: Optional[int] = TicketHandler.parse_ticket_number(order_in.name)
        if not ticket_number:
            ticket_number = self.ticket_handler.create_ticket(
                order=order_in, user_name=user_name, user_mail=user_mail, project=project
            )

        order_in.ticket = ticket_number

        order_func = self._get_submit_func(project.value)
        return order_func(order_in)

    def validate_order(self, order_in: OrderIn, project: OrderType):
        self._validate_samples_available_to_customer(
            project=project, samples=order_in.samples, customer_id=order_in.customer
        )
        self._validate_case_names_are_unique(
            project=project, samples=order_in.samples, customer_id=order_in.customer
        )
        self._validate_subject_sex(samples=order_in.samples, customer_id=order_in.customer)

    def _submit_fluffy(self, order: OrderIn) -> dict:
        """Submit a batch of ready made libraries for FLUFFY analysis."""
        return self._submit_pools(order)

    def _submit_rml(self, order: OrderIn) -> dict:
        """Submit a batch of ready made libraries for sequencing."""
        return self._submit_pools(order)

    def _submit_pools(self, order: OrderIn):
        status_data = self.pools_to_status(order)
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order.samples
        )
        samples = [sample for pool in status_data["pools"] for sample in pool["samples"]]
        self._fill_in_sample_ids(samples, lims_map, id_key="internal_id")
        new_records = self.store_rml(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=order.ticket,
            pools=status_data["pools"],
        )
        return {"project": project_data, "records": new_records}

    def _submit_fastq(self, order: OrderIn) -> dict:
        """Submit a batch of samples for FASTQ delivery."""
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order.samples
        )
        status_data = self.fastq_to_status(order)
        self._fill_in_sample_ids(status_data["samples"], lims_map)
        new_samples = self.store_fastq_samples(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=order.ticket,
            samples=status_data["samples"],
        )
        self._add_missing_reads(new_samples)
        return {"project": project_data, "records": new_samples}

    def _submit_metagenome(self, order: OrderIn) -> dict:
        """Submit a batch of metagenome samples."""
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order.samples
        )
        status_data = self.metagenome_to_status(order)
        self._fill_in_sample_ids(status_data["samples"], lims_map)
        new_samples = self.store_metagenome(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=order.ticket,
            samples=status_data["samples"],
        )
        self._add_missing_reads(new_samples)
        return {"project": project_data, "records": new_samples}

    def _submit_case_samples(self, order: OrderIn, project: OrderType) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        result = self._process_case_samples(order=order, project=project)
        for case_obj in result["records"]:
            LOG.info(f"{case_obj.name}: submit family samples")
            status_samples = [
                link_obj.sample
                for link_obj in case_obj.links
                if link_obj.sample.ticket_number == order.ticket
            ]
            self._add_missing_reads(status_samples)
        return result

    def _submit_mip_dna(self, order: OrderIn) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        return self._submit_case_samples(order=order, project=OrderType.MIP_DNA)

    def _submit_balsamic(self, order: OrderIn) -> dict:
        """Submit a batch of samples for sequencing and balsamic analysis."""
        return self._submit_case_samples(order=order, project=OrderType.BALSAMIC)

    def _submit_mip_rna(self, order: OrderIn) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        return self._submit_case_samples(order=order, project=OrderType.MIP_RNA)

    def _submit_microsalt(self, order: OrderIn) -> dict:
        """Submit a batch of microbial samples."""
        return self._submit_microbial_samples(order)

    def _submit_microbial_samples(self, order: OrderIn):
        self._fill_in_sample_verified_organism(order.samples)
        # submit samples to LIMS
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order.samples
        )
        # prepare order for status database
        status_data = self.microbial_samples_to_status(order)
        self._fill_in_sample_ids(status_data["samples"], lims_map, id_key="internal_id")
        # submit samples to Status
        samples = self.store_microbial_samples(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"] if project_data else dt.datetime.now(),
            ticket=order.ticket,
            samples=status_data["samples"],
            comment=status_data["comment"],
            data_analysis=Pipeline(status_data["data_analysis"]),
            data_delivery=DataDelivery(status_data["data_delivery"]),
        )
        return {"project": project_data, "records": samples}

    def _submit_sars_cov_2(self, order: OrderIn) -> dict:
        """Submit a batch of sars-cov-2 samples."""
        # prepare order for status database
        return self._submit_microbial_samples(order)

    def _process_case_samples(self, order: OrderIn, project: OrderType) -> dict:
        """Process samples to be analyzed."""
        project_data = lims_map = None

        # submit new samples to lims
        new_samples = [sample for sample in order.samples if sample.internal_id is None]
        if new_samples:
            project_data, lims_map = process_lims(
                lims_api=self.lims, lims_order=order, new_samples=new_samples
            )

        status_data = self.cases_to_status(order=order, project=project)
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

    def _add_missing_reads(self, samples: List[models.Sample]):
        """Add expected reads/reads missing."""
        for sample_obj in samples:
            LOG.info(f"{sample_obj.internal_id}: add missing reads in LIMS")
            target_reads = sample_obj.application_version.application.target_reads / 1000000
            self.lims.update_sample(sample_obj.internal_id, target_reads=target_reads)

    @staticmethod
    def _fill_in_sample_ids(samples: List[dict], lims_map: dict, id_key: str = "internal_id"):
        """Fill in LIMS sample ids."""
        for sample in samples:
            LOG.debug(f"{sample['name']}: link sample to LIMS")
            if not sample.get(id_key):
                internal_id = lims_map[sample["name"]]
                LOG.info(f"{sample['name']} -> {internal_id}: connect sample to LIMS")
                sample[id_key] = internal_id

    def _fill_in_sample_verified_organism(self, samples: List[MicrobialSample]):
        for sample in samples:
            organism_id = sample.organism
            reference_genome = sample.reference_genome
            organism = self.status.organism(internal_id=organism_id)
            is_verified = (
                organism and organism.reference_genome == reference_genome and organism.verified
            )
            sample.verified_organism = is_verified

    def _validate_samples_available_to_customer(
        self, project: OrderType, samples: List[OrderInSample], customer_id: str
    ) -> None:
        """Validate that the customer have access to all samples"""
        if project not in (
            OrderType.BALSAMIC,
            OrderType.MIP_DNA,
            OrderType.MIP_RNA,
        ):
            return

        sample: Of1508Sample
        for sample in samples:
            if not sample.internal_id:
                continue

            existing_sample: models.Sample = self.status.sample(sample.internal_id)
            data_customer: models.Customer = self.status.customer(customer_id)

            if existing_sample.customer.customer_group_id != data_customer.customer_group_id:
                raise OrderError(f"Sample not available: {sample.name}")

    def _validate_case_names_are_unique(
        self, project: OrderType, samples: List[OrderInSample], customer_id: str
    ) -> None:
        """Validate that the names of all cases are unused for all samples"""
        customer_obj: models.Customer = self.status.customer(customer_id)
        if project not in (
            OrderType.BALSAMIC,
            OrderType.MIP_DNA,
            OrderType.MIP_RNA,
        ):
            return

        sample: Of1508Sample
        for sample in samples:

            if self._rerun_of_existing_case(sample):
                continue

            if self.status.find_family(customer=customer_obj, name=sample.family_name):
                raise OrderError(f"Case name {sample.family_name} already in use")

    @staticmethod
    def _rerun_of_existing_case(sample: Of1508Sample) -> bool:
        return sample.case_internal_id is not None

    def _get_submit_func(self, project_type: OrderType) -> typing.Callable:
        """Get the submit method to call for the given type of project"""

        if project_type == OrderType.MIP_DNA:
            return getattr(self, "_submit_mip_dna")
        if project_type == OrderType.MIP_RNA:
            return getattr(self, "_submit_mip_rna")
        if project_type == OrderType.SARS_COV_2:
            return getattr(self, "_submit_sars_cov_2")

        return getattr(self, f"_submit_{str(project_type)}")

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
            if not isinstance(sample, Of1508Sample):
                continue

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

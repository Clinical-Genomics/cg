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
from cg.models.orders.order import OrderIn
from cg.store import Store, models

from .lims import process_lims
from .schema import ORDER_SCHEMES, OrderType
from .status import StatusHandler
from .ticket_handler import TicketHandler

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
        try:
            ORDER_SCHEMES[project].validate(order_in.dict())
        except (ValueError, TypeError) as error:
            raise OrderError(str(error))

        self._validate_samples_available_to_customer(
            project=project, samples=order_in.samples, customer_id=order_in.customer
        )
        self._validate_case_names_are_unique(
            samples=order_in.samples, customer_id=order_in.customer
        )

        # detect manual ticket assignment
        ticket_number: Optional[int] = TicketHandler.parse_ticket_number(order_in.name)
        if not ticket_number:
            ticket_number = self.ticket_handler.create_ticket(
                order=order_in, user_name=user_name, user_mail=user_mail, project=project
            )

        order = order_in.dict()
        order["ticket"] = ticket_number

        order_func = self._get_submit_func(project.value)
        return order_func(order)

    def _submit_fluffy(self, order: dict) -> dict:
        """Submit a batch of ready made libraries for FLUFFY analysis."""
        return self._submit_pools(order)

    def _submit_rml(self, order: dict) -> dict:
        """Submit a batch of ready made libraries for sequencing."""
        return self._submit_pools(order)

    def _submit_pools(self, order):
        status_data = self.pools_to_status(order)
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order["samples"]
        )
        samples = [sample for pool in status_data["pools"] for sample in pool["samples"]]
        self._fill_in_sample_ids(samples, lims_map, id_key="internal_id")
        new_records = self.store_rml(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=order["ticket"],
            pools=status_data["pools"],
        )
        return {"project": project_data, "records": new_records}

    def _submit_fastq(self, order: dict) -> dict:
        """Submit a batch of samples for FASTQ delivery."""
        status_data = self.samples_to_status(order)
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order["samples"]
        )
        self._fill_in_sample_ids(status_data["samples"], lims_map)
        new_samples = self.store_fastq_samples(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=order["ticket"],
            samples=status_data["samples"],
        )
        self._add_missing_reads(new_samples)
        return {"project": project_data, "records": new_samples}

    def _submit_metagenome(self, order: dict) -> dict:
        """Submit a batch of metagenome samples."""
        status_data = self.samples_to_status(order)
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order["samples"]
        )
        self._fill_in_sample_ids(status_data["samples"], lims_map)
        new_samples = self.store_samples(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=order["ticket"],
            samples=status_data["samples"],
        )
        self._add_missing_reads(new_samples)
        return {"project": project_data, "records": new_samples}

    def _submit_external(self, order: dict) -> dict:
        """Submit a batch of externally sequenced samples for analysis."""
        return self._process_case_samples(order)

    def _submit_case_samples(self, order: dict) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        result = self._process_case_samples(order)
        for case_obj in result["records"]:
            LOG.info(f"{case_obj.name}: submit family samples")
            status_samples = [
                link_obj.sample
                for link_obj in case_obj.links
                if link_obj.sample.ticket_number == order["ticket"]
            ]
            self._add_missing_reads(status_samples)
        self._update_application(order["ticket"], result["records"])
        return result

    def _submit_mip_dna(self, order: dict) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        return self._submit_case_samples(order)

    def _submit_balsamic(self, order: dict) -> dict:
        """Submit a batch of samples for sequencing and balsamic analysis."""
        return self._submit_case_samples(order)

    def _submit_mip_rna(self, order: dict) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        return self._submit_case_samples(order)

    def _submit_microsalt(self, order: dict) -> dict:
        """Submit a batch of microbial samples."""
        return self._submit_microbial_samples(order)

    def _submit_microbial_samples(self, order):
        # prepare order for status database
        status_data = self.microbial_samples_to_status(order)
        self._fill_in_sample_verified_organism(order["samples"])
        # submit samples to LIMS
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order["samples"]
        )
        self._fill_in_sample_ids(status_data["samples"], lims_map, id_key="internal_id")
        # submit samples to Status
        samples = self.store_microbial_samples(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"] if project_data else dt.datetime.now(),
            ticket=order["ticket"],
            samples=status_data["samples"],
            comment=status_data["comment"],
            data_analysis=Pipeline(status_data["data_analysis"]),
            data_delivery=DataDelivery(status_data["data_delivery"]),
        )
        return {"project": project_data, "records": samples}

    def _submit_sars_cov_2(self, order: dict) -> dict:
        """Submit a batch of sars-cov-2 samples."""
        # prepare order for status database
        return self._submit_microbial_samples(order)

    def _process_case_samples(self, order: dict) -> dict:
        """Process samples to be analyzed."""
        # filter out only new samples
        status_data = self.cases_to_status(order)
        new_samples = [sample for sample in order["samples"] if sample.get("internal_id") is None]
        if new_samples:
            project_data, lims_map = process_lims(
                lims_api=self.lims, lims_order=order, new_samples=new_samples
            )
        else:
            project_data = lims_map = None
        samples = [sample for family in status_data["families"] for sample in family["samples"]]
        if lims_map:
            self._fill_in_sample_ids(samples, lims_map)
        new_families = self.store_cases(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"] if project_data else dt.datetime.now(),
            ticket=order["ticket"],
            cases=status_data["families"],
        )
        return {"project": project_data, "records": new_families}

    def _update_application(self, ticket_number: int, families: List[models.Family]) -> None:
        """Update application for trios if relevant."""
        reduced_map = {
            "EXOSXTR100": "EXTSXTR100",
            "WGSPCFC030": "WGTPCFC030",
        }
        for case_obj in families:
            LOG.debug(f"{case_obj.name}: update application for trios")
            order_samples = [
                link_obj.sample
                for link_obj in case_obj.links
                if link_obj.sample.ticket_number == ticket_number
            ]
            if len(order_samples) >= 3:
                applications = [
                    sample_obj.application_version.application for sample_obj in order_samples
                ]
                prep_categories = {application.prep_category for application in applications}
                if len(prep_categories) == 1:
                    for sample_obj in order_samples:
                        if not sample_obj.application_version.application.reduced_price:
                            application_tag = sample_obj.application_version.application.tag
                            if application_tag in reduced_map:
                                reduced_tag = reduced_map[application_tag]
                                LOG.info(
                                    f"{sample_obj.internal_id}: update application tag - "
                                    f"{reduced_tag}"
                                )
                                reduced_version = self.status.current_application_version(
                                    reduced_tag
                                )
                                sample_obj.application_version = reduced_version

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

    def _fill_in_sample_verified_organism(self, samples: List[dict]):
        for sample in samples:
            organism_id = sample["organism"]
            reference_genome = sample["reference_genome"]
            organism = self.status.organism(internal_id=organism_id)
            is_verified = (
                organism and organism.reference_genome == reference_genome and organism.verified
            )
            sample["verified_organism"] = is_verified

    def _validate_samples_available_to_customer(
        self, project: OrderType, samples: List[dict], customer_id: str
    ) -> None:
        """Validate that the customer have access to all samples"""
        for sample in samples:

            if sample.get("internal_id"):

                if project not in (
                    OrderType.BALSAMIC,
                    OrderType.EXTERNAL,
                    OrderType.MIP_DNA,
                    OrderType.MIP_RNA,
                ):
                    raise OrderError(
                        f"Only MIP, Balsamic and external orders can have imported "
                        f"samples: "
                        f"{sample.get('name')}"
                    )

                existing_sample: models.Sample = self.status.sample(sample.get("internal_id"))
                data_customer: models.Customer = self.status.customer(customer_id)

                if existing_sample.customer.customer_group_id != data_customer.customer_group_id:
                    raise OrderError(f"Sample not available: {sample.get('name')}")

    def _validate_case_names_are_unique(self, samples: List[dict], customer_id: str) -> None:
        """Validate that the names of all cases are unused for all samples"""
        customer_obj: models.Customer = self.status.customer(customer_id)

        for sample in samples:

            case_id: str = sample.get("family_name")

            if self._existing_case_or_orders_without_explicit_case_name(sample, case_id):
                continue

            if self.status.find_family(customer=customer_obj, name=case_id):
                raise OrderError(f"Case name {case_id} already in use for customer {customer_id}")

    @staticmethod
    def _existing_case_or_orders_without_explicit_case_name(sample: dict, case_id: str) -> bool:
        return sample.get("case_internal_id") or not case_id

    def _get_submit_func(self, project_type: OrderType) -> typing.Callable:
        """Get the submit method to call for the given type of project"""

        if project_type == OrderType.MIP_DNA:
            return getattr(self, "_submit_mip_dna")
        if project_type == OrderType.MIP_RNA:
            return getattr(self, "_submit_mip_rna")
        if project_type == OrderType.SARS_COV_2:
            return getattr(self, "_submit_sars_cov_2")

        return getattr(self, f"_submit_{str(project_type)}")

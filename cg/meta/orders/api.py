"""Unified interface to handle sample submissions.

This interface will update information in Status and/or LIMS as required.

The normal entry for information is through the REST API which will pass a JSON
document with all information about samples in the submission. The input will
be validated and if passing all checks be accepted as new samples.
"""
import datetime as dt
import logging
import re
import typing
from typing import List

from cg.apps.lims import LimsAPI
from cg.apps.osticket import OsTicket
from cg.constants import DataDelivery, Pipeline
from cg.exc import OrderError, TicketCreationError
from cg.store import Store, models

from .lims import LimsHandler
from .schema import ORDER_SCHEMES, OrderType
from .status import StatusHandler

LOG = logging.getLogger(__name__)
NEW_LINE = "<br />"


class OrdersAPI(LimsHandler, StatusHandler):
    """Orders API for accepting new samples into the system."""

    def __init__(self, lims: LimsAPI, status: Store, osticket: OsTicket = None):
        super().__init__()
        self.lims = lims
        self.status = status
        self.osticket = osticket

    def submit(self, project: OrderType, order: dict, ticket: dict) -> dict:
        """Submit a batch of samples.

        Main entry point for the class towards interfaces that implements it.
        """
        try:
            ORDER_SCHEMES[project].validate(order)
        except (ValueError, TypeError) as error:
            raise OrderError(error.args[0])

        self._validate_customer_on_imported_samples(project, order)

        # detect manual ticket assignment
        ticket_match = re.fullmatch(r"#([0-9]{6})", order["name"])

        if ticket_match:
            ticket_number = int(ticket_match.group(1))
            LOG.info(f"{ticket_number}: detected ticket in order name")
            order["ticket"] = ticket_number
        else:
            # open and assign ticket to order
            try:
                if self.osticket:
                    message = self._create_new_ticket_message(
                        order=order, ticket=ticket, project=project
                    )

                    order["ticket"] = self.osticket.open_ticket(
                        name=ticket["name"],
                        email=ticket["email"],
                        subject=order["name"],
                        message=message,
                    )

                    LOG.info(f"{order['ticket']}: opened new ticket")
                else:
                    order["ticket"] = None
            except TicketCreationError as error:
                LOG.warning(error.message)
                order["ticket"] = None
        order_func = self._get_submit_func(project.value)
        result = order_func(order)
        return result

    def _create_new_ticket_message(self, order: dict, ticket: dict, project: str) -> str:
        message = (
            f"data:text/html;charset=utf-8,New incoming {order.get('data_analysis')} samples: "
        )

        for sample in order.get("samples"):
            message = self._add_sample_name_to_message(message, sample)
            message = self._add_sample_apptag_to_message(message, sample)
            message = self._add_sample_case_name_to_message(message, sample)
            message = self._add_existing_sample_info_to_message(message, order, sample)
            message = self._add_sample_priority_to_message(message, sample)
            message = self._add_sample_comment_to_message(message, sample)

        message += NEW_LINE
        message = self._add_project_to_message(message, project)
        message = self._add_data_delivery_to_message(order, message)
        message = self._add_comment_to_message(order, message)
        message = self._add_user_name_to_message(message, ticket)
        message = self._add_customer_to_message(order, message)

        return message

    @staticmethod
    def _add_sample_name_to_message(message, sample):
        message += NEW_LINE + sample.get("name")
        return message

    @staticmethod
    def _add_sample_apptag_to_message(message, sample):
        if sample.get("application"):
            message += f", application: {sample['application']}"
        return message

    @staticmethod
    def _add_sample_case_name_to_message(message, sample):
        if sample.get("family_name"):
            message += f", case: {sample.get('family_name')}"
        return message

    def _add_existing_sample_info_to_message(self, message, order, sample):
        if sample.get("internal_id"):

            existing_sample = self.status.sample(sample.get("internal_id"))
            sample_customer = ""
            if existing_sample.customer_id != order["customer"]:
                sample_customer = " from " + existing_sample.customer.internal_id

            message += f" (already existing sample{sample_customer})"
        return message

    @staticmethod
    def _add_sample_priority_to_message(message, sample):
        if sample.get("priority"):
            message += ", priority: " + sample.get("priority")
        return message

    @staticmethod
    def _add_sample_comment_to_message(message, sample):
        if sample.get("comment"):
            message += ", " + sample.get("comment")
        return message

    @staticmethod
    def _add_project_to_message(message, project):
        if project:
            message += NEW_LINE + f"{project}."
        return message

    @staticmethod
    def _add_data_delivery_to_message(order, message):
        if order.get("delivery"):
            message += NEW_LINE + f"{order.get('delivery')}."
        return message

    @staticmethod
    def _add_comment_to_message(order, message):
        if order.get("comment"):
            message += NEW_LINE + f"{order.get('comment')}."
        return message

    @staticmethod
    def _add_user_name_to_message(message, ticket):
        if ticket.get("name"):
            message += NEW_LINE + f"{ticket.get('name')}"
        return message

    def _add_customer_to_message(self, order, message):
        if order.get("customer"):
            customer_id = order.get("customer")
            customer_name = self.status.customer(customer_id).name

            message += f", {customer_name} ({customer_id})"
        return message

    def _submit_fluffy(self, order: dict) -> dict:
        """Submit a batch of ready made libraries for FLUFFY analysis."""
        return self._submit_pools(order)

    def _submit_rml(self, order: dict) -> dict:
        """Submit a batch of ready made libraries for sequencing."""
        return self._submit_pools(order)

    def _submit_pools(self, order):
        status_data = self.pools_to_status(order)
        project_data, lims_map = self.process_lims(order, order["samples"])
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
        project_data, lims_map = self.process_lims(order, order["samples"])
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
        project_data, lims_map = self.process_lims(order, order["samples"])
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
        result = self._process_case_samples(order)
        return result

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
        # prepare order for status database
        status_data = self.microbial_samples_to_status(order)
        self._fill_in_sample_verified_organism(order["samples"])
        # submit samples to LIMS
        project_data, lims_map = self.process_lims(order, order["samples"])
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

    def _process_case_samples(self, order: dict) -> dict:
        """Process samples to be analyzed."""
        # filter out only new samples
        status_data = self.cases_to_status(order)
        new_samples = [sample for sample in order["samples"] if sample.get("internal_id") is None]
        if new_samples:
            project_data, lims_map = self.process_lims(order, new_samples)
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
                prep_categories = set(application.prep_category for application in applications)
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

    def _validate_customer_on_imported_samples(self, project: OrderType, order: dict):
        for sample in order.get("samples"):

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

                existing_sample = self.status.sample(sample.get("internal_id"))
                data_customer = self.status.customer(order["customer"])

                if existing_sample.customer.customer_group_id != data_customer.customer_group_id:
                    raise OrderError(f"Sample not available: {sample.get('name')}")

    def _get_submit_func(self, project_type: OrderType) -> typing.Callable:
        """Get the submit method to call for the given type of project"""

        if project_type == OrderType.MIP_DNA:
            return getattr(self, "_submit_mip_dna")
        if project_type == OrderType.MIP_RNA:
            return getattr(self, "_submit_mip_rna")

        return getattr(self, f"_submit_{str(project_type)}")

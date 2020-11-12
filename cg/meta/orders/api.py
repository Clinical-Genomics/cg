"""Unified interface to handle sample submissions.

This interface will update information in Status and/or LIMS as required.

The normal entry for information is through the REST API which will pass a JSON
document with all information about samples in the submission. The input will
be validated and if passing all checks be accepted as new samples.
"""
import datetime as dt
import logging
import re
from typing import List

import typing
from cg.apps.lims import LimsAPI
from cg.apps.osticket import OsTicket
from cg.constants import Pipeline
from cg.exc import OrderError, TicketCreationError
from cg.store import Store, models
from .schema import OrderType, ORDER_SCHEMES
from .lims import LimsHandler
from .status import StatusHandler

LOG = logging.getLogger(__name__)


class OrdersAPI(LimsHandler, StatusHandler):
    """Orders API for accepting new samples into the system."""

    def __init__(self, lims: LimsAPI, status: Store, osticket: OsTicket = None):
        super().__init__()
        self.lims = lims
        self.status = status
        self.osticket = osticket

    def submit(self, project: OrderType, data: dict, ticket: dict) -> dict:
        """Submit a batch of samples.

        Main entry point for the class towards interfaces that implements it.
        """
        try:
            ORDER_SCHEMES[project].validate(data)
        except (ValueError, TypeError) as error:
            raise OrderError(error.args[0])

        self._validate_customer_on_imported_samples(project, data)

        # detect manual ticket assignment
        ticket_match = re.fullmatch(r"#([0-9]{6})", data["name"])

        if ticket_match:
            ticket_number = int(ticket_match.group(1))
            LOG.info(f"{ticket_number}: detected ticket in order name")
            data["ticket"] = ticket_number
        else:
            # open and assign ticket to order
            try:
                if self.osticket:
                    message = f"data:text/html;charset=utf-8,New incoming samples: "

                    for sample in data.get("samples"):
                        message += "<br />" + sample.get("name")

                        if sample.get("application"):
                            message += f", application: {sample.get('application')}"

                        if sample.get("family_name"):
                            message += f", family: {sample.get('family_name')}"

                        if sample.get("internal_id"):

                            existing_sample = self.status.sample(sample.get("internal_id"))
                            sample_customer = ""
                            if existing_sample.customer_id != data["customer"]:
                                sample_customer = " from " + existing_sample.customer.internal_id

                            message += f" (already existing sample{sample_customer})"

                        if sample.get("comment"):
                            message += ", " + sample.get("comment")

                    message += f"<br />"

                    if data.get("comment"):
                        message += f"<br />{data.get('comment')}."

                    if ticket.get("name"):
                        message += f"<br />{ticket.get('name')}"

                    data["ticket"] = self.osticket.open_ticket(
                        name=ticket["name"],
                        email=ticket["email"],
                        subject=data["name"],
                        message=message,
                    )

                    LOG.info(f"{data['ticket']}: opened new ticket")
                else:
                    data["ticket"] = None
            except TicketCreationError as error:
                LOG.warning(error.message)
                data["ticket"] = None
        order_func = self._get_submit_func(project.value)
        result = order_func(data)
        return result

    def submit_rml(self, data: dict) -> dict:
        """Submit a batch of ready made libraries."""
        status_data = self.pools_to_status(data)
        project_data, _ = self.process_lims(data, data["samples"])
        new_records = self.store_pools(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=data["ticket"],
            pools=status_data["pools"],
        )
        return {"project": project_data, "records": new_records}

    def submit_fastq(self, data: dict) -> dict:
        """Submit a batch of samples for FASTQ delivery."""
        status_data = self.samples_to_status(data)
        project_data, lims_map = self.process_lims(data, data["samples"])
        self.fill_in_sample_ids(status_data["samples"], lims_map)
        new_samples = self.store_fastq_samples(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=data["ticket"],
            samples=status_data["samples"],
        )
        self.add_missing_reads(new_samples)
        return {"project": project_data, "records": new_samples}

    def submit_metagenome(self, data: dict) -> dict:
        """Submit a batch of metagenome samples."""
        status_data = self.samples_to_status(data)
        project_data, lims_map = self.process_lims(data, data["samples"])
        self.fill_in_sample_ids(status_data["samples"], lims_map)
        new_samples = self.store_samples(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=data["ticket"],
            samples=status_data["samples"],
        )
        self.add_missing_reads(new_samples)
        return {"project": project_data, "records": new_samples}

    def submit_external(self, data: dict) -> dict:
        """Submit a batch of externally sequenced samples for analysis."""
        result = self.process_family_samples(data)
        return result

    def submit_case_samples(self, data: dict) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        result = self.process_family_samples(data)
        for family_obj in result["records"]:
            LOG.info(f"{family_obj.name}: submit family samples")
            status_samples = [
                link_obj.sample
                for link_obj in family_obj.links
                if link_obj.sample.ticket_number == data["ticket"]
            ]
            self.add_missing_reads(status_samples)
        self.update_application(data["ticket"], result["records"])
        return result

    def submit_mip_dna(self, data: dict) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        return self.submit_case_samples(data)

    def submit_balsamic(self, data: dict) -> dict:
        """Submit a batch of samples for sequencing and balsamic analysis."""
        return self.submit_case_samples(data)

    def submit_mip_rna(self, data: dict) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        return self.submit_case_samples(data)

    def submit_microsalt(self, data: dict) -> dict:
        """Submit a batch of microbial samples."""
        # prepare data for status database
        status_data = self.microbial_samples_to_status(data)
        self.fill_in_sample_verified_organism(data["samples"])
        # submit samples to LIMS
        project_data, lims_map = self.process_lims(data, data["samples"])
        self.fill_in_sample_ids(status_data["samples"], lims_map, id_key="internal_id")
        # submit samples to Status
        samples = self.store_microbial_samples(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"] if project_data else dt.datetime.now(),
            ticket=data["ticket"],
            samples=status_data["samples"],
            comment=status_data["comment"],
            data_analysis=Pipeline(status_data["data_analysis"]),
        )

        return {"project": project_data, "records": samples}

    def process_family_samples(self, data: dict) -> dict:
        """Process samples to be analyzed."""
        # filter out only new samples
        status_data = self.cases_to_status(data)
        new_samples = [sample for sample in data["samples"] if sample.get("internal_id") is None]
        if new_samples:
            project_data, lims_map = self.process_lims(data, new_samples)
        else:
            project_data = lims_map = None
        samples = [sample for family in status_data["families"] for sample in family["samples"]]
        if lims_map:
            self.fill_in_sample_ids(samples, lims_map)
        new_families = self.store_cases(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"] if project_data else dt.datetime.now(),
            ticket=data["ticket"],
            cases=status_data["families"],
        )
        return {"project": project_data, "records": new_families}

    def update_application(self, ticket_number: int, families: List[models.Family]) -> None:
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

    def add_missing_reads(self, samples: List[models.Sample]):
        """Add expected reads/reads missing."""
        for sample_obj in samples:
            LOG.info(f"{sample_obj.internal_id}: add missing reads in LIMS")
            target_reads = sample_obj.application_version.application.target_reads / 1000000
            self.lims.update_sample(sample_obj.internal_id, target_reads=target_reads)

    @staticmethod
    def fill_in_sample_ids(samples: List[dict], lims_map: dict, id_key: str = "internal_id"):
        """Fill in LIMS sample ids."""
        for sample in samples:
            LOG.debug(f"{sample['name']}: link sample to LIMS")
            if not sample.get(id_key):
                internal_id = lims_map[sample["name"]]
                LOG.info(f"{sample['name']} -> {internal_id}: connect sample to LIMS")
                sample[id_key] = internal_id

    def fill_in_sample_verified_organism(self, samples: List[dict]):
        for sample in samples:
            organism_id = sample["organism"]
            reference_genome = sample["reference_genome"]
            organism = self.status.organism(internal_id=organism_id)
            is_verified = (
                organism and organism.reference_genome == reference_genome and organism.verified
            )
            sample["verified_organism"] = is_verified

    def _validate_customer_on_imported_samples(self, project, data):
        for sample in data.get("samples"):

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
                data_customer = self.status.customer(data["customer"])

                if existing_sample.customer.customer_group_id != data_customer.customer_group_id:
                    raise OrderError(f"Sample not available: {sample.get('name')}")

    def _get_submit_func(self, project_type: OrderType) -> typing.Callable:
        """Get the submit method to call for the given type of project"""

        if project_type == OrderType.MIP_DNA:
            return getattr(self, "submit_mip_dna")
        elif project_type == OrderType.MIP_RNA:
            return getattr(self, "submit_mip_rna")

        return getattr(self, f"submit_{str(project_type)}")

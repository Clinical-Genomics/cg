import logging
import re
from typing import Optional

from cg.apps.osticket import OsTicket
from cg.exc import TicketCreationError
from cg.server.schemas.order import OrderIn
from cg.store import Store, models

LOG = logging.getLogger(__name__)


class TicketHandler:
    """Handle tickets in the meta orders context"""

    NEW_LINE = "<br />"

    def __init__(self, osticket_api: OsTicket, status_db: Store):
        self.osticket: OsTicket = osticket_api
        self.status_db: Store = status_db

    @staticmethod
    def parse_ticket_number(name: str) -> Optional[int]:
        """Try to parse a ticket number from a string"""
        # detect manual ticket assignment
        ticket_match = re.fullmatch(r"#([0-9]{6})", name)
        if ticket_match:
            ticket_number = int(ticket_match.group(1))
            LOG.info("%s: detected ticket in order name", ticket_number)
            return ticket_number
        LOG.info("Could not detected ticket number in name %s", name)
        return None

    def create_ticket(
        self, order: OrderIn, user_name: str, user_mail: str, project: str
    ) -> Optional[int]:
        """Create a ticket and return the ticket number"""
        message = self.create_new_ticket_message(order=order, user_name=user_name, project=project)
        ticket_nr = None
        try:
            ticket_nr: int = self.osticket.open_ticket(
                name=user_name,
                email=user_mail,
                subject=order.name,
                message=message,
            )

            LOG.info(f"{ticket_nr}: opened new ticket")
        except TicketCreationError as error:
            LOG.warning(error.message)

        return ticket_nr

    def create_new_ticket_message(self, order: OrderIn, user_name: str, project: str) -> str:
        message = f"data:text/html;charset=utf-8,New incoming {project} samples: "

        for sample in order.samples:
            self.add_sample_name_to_message(message=message, sample_name=sample.get("name"))
            self.add_sample_apptag_to_message(
                message=message, application=sample.get("application")
            )
            self.add_sample_case_name_to_message(
                message=message, case_name=sample.get("family_name")
            )
            self.add_existing_sample_info_to_message(
                message=message, customer_id=order.customer, internal_id=sample.get("internal_id")
            )
            self.add_sample_priority_to_message(message=message, priority=sample.get("priority"))
            self.add_sample_comment_to_message(message=message, comment=sample.get("comment"))

        message += self.NEW_LINE
        self.add_order_comment_to_message(message=message, comment=order.comment)
        self.add_user_name_to_message(message=message, name=user_name)
        self.add_customer_to_message(message=message, customer_id=order.customer)

        return message

    def add_sample_name_to_message(self, message: str, sample_name: str) -> None:
        message += self.NEW_LINE + sample_name

    @staticmethod
    def add_sample_apptag_to_message(message: str, application: Optional[str]) -> None:
        if application:
            message += f", application: {application}"

    @staticmethod
    def add_sample_case_name_to_message(message: str, case_name: Optional[str]):
        if case_name:
            message += f", case: {case_name}"

    def add_existing_sample_info_to_message(
        self, message: str, customer_id: str, internal_id: Optional[str]
    ) -> None:
        if not internal_id:
            return
        existing_sample: models.Sample = self.status_db.sample(internal_id)
        sample_customer = ""
        if existing_sample.customer_id != customer_id:
            sample_customer = " from " + existing_sample.customer.internal_id

        message += f" (already existing sample{sample_customer})"

    @staticmethod
    def add_sample_priority_to_message(message: str, priority: Optional[str]) -> None:
        if priority:
            message += ", priority: " + priority

    @staticmethod
    def add_sample_comment_to_message(message: str, comment: Optional[str]) -> None:
        if comment:
            message += ", " + comment

    def add_order_comment_to_message(self, message: str, comment: Optional[str]) -> None:
        if not comment:
            return
        message += self.NEW_LINE + f"{comment}."

    def add_user_name_to_message(self, message: str, name: Optional[str]):
        if not name:
            return
        message += self.NEW_LINE + f"{name}"

    def add_customer_to_message(self, message: str, customer_id: str) -> None:
        customer: models.Customer = self.status_db.customer(customer_id)
        message += f", {customer.name} ({customer_id})"

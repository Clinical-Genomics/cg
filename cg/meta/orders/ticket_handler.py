import logging
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from sendmail_container import FormDataRequest

from cg.apps.osticket import OsTicket
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import Of1508Sample
from cg.store.models import Customer, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class TicketHandler:
    """Handle tickets in the meta orders context"""

    NEW_LINE = "<br />"

    def __init__(self, osticket_api: OsTicket, status_db: Store):
        self.osticket: OsTicket = osticket_api
        self.status_db: Store = status_db

    @staticmethod
    def parse_ticket_number(name: str) -> str | None:
        """Try to parse a ticket number from a string"""
        # detect manual ticket assignment
        ticket_match = re.fullmatch(r"#([0-9]{6})", name)
        if ticket_match:
            ticket_id = ticket_match.group(1)
            LOG.info(f"{ticket_id}: detected ticket in order name")
            return ticket_id
        LOG.info(f"Could not detected ticket number in name {name}")
        return None

    def create_ticket(
        self, order: OrderIn, user_name: str, user_mail: str, project: str
    ) -> int | None:
        """Create a ticket and return the ticket number"""
        message: str = self.create_new_ticket_header(
            message=self.create_xml_sample_list(order=order, user_name=user_name),
            order=order,
            project=project,
        )
        attachment: dict = self.create_attachment(order=order)
        ticket_nr: str | None = self.osticket.open_ticket(
            name=user_name,
            email=user_mail,
            subject=order.name,
            message=message,
            attachment=attachment,
        )
        LOG.info(f"{ticket_nr}: opened new ticket")

        return ticket_nr

    def create_attachment(self, order: OrderIn):
        return self.osticket.create_new_ticket_attachment(
            content=self.replace_empty_string_with_none(obj=order.dict()), file_name="order.json"
        )

    def create_xml_sample_list(self, order: OrderIn, user_name: str) -> str:
        message = ""
        for sample in order.samples:
            message = self.add_sample_name_to_message(message=message, sample_name=sample.name)
            message = self.add_sample_apptag_to_message(
                message=message, application=sample.application
            )
            if isinstance(sample, Of1508Sample):
                message = self.add_sample_case_name_to_message(
                    message=message, case_name=sample.family_name
                )
                message = self.add_existing_sample_info_to_message(
                    message=message, customer_id=order.customer, internal_id=sample.internal_id
                )
            message = self.add_sample_priority_to_message(message=message, priority=sample.priority)
            message = self.add_sample_comment_to_message(message=message, comment=sample.comment)

        message += self.NEW_LINE
        message = self.add_order_comment_to_message(message=message, comment=order.comment)
        message = self.add_user_name_to_message(message=message, name=user_name)
        message = self.add_customer_to_message(message=message, customer_id=order.customer)

        return message

    @staticmethod
    def create_new_ticket_header(message: str, order: OrderIn, project: str) -> str:
        return (
            f"data:text/html;charset=utf-8, New order with {len(order.samples)} {project} samples:"
            + message
        )

    @staticmethod
    def add_existing_ticket_header(message: str, order: OrderIn, project: str) -> str:
        return (
            f"A new order with {len(order.samples)} {project} samples has been connected to this ticket:"
            + message
        )

    def add_sample_name_to_message(self, message: str, sample_name: str) -> str:
        message += f"{self.NEW_LINE}{sample_name}"
        return message

    @staticmethod
    def add_sample_apptag_to_message(message: str, application: str | None) -> str:
        if application:
            message += f", application: {application}"
        return message

    @staticmethod
    def add_sample_case_name_to_message(message: str, case_name: str | None) -> str:
        if case_name:
            message += f", case: {case_name}"
        return message

    def add_existing_sample_info_to_message(
        self, message: str, customer_id: str, internal_id: str | None
    ) -> str:
        if not internal_id:
            return message

        existing_sample: Sample = self.status_db.get_sample_by_internal_id(internal_id=internal_id)

        sample_customer = ""
        if existing_sample.customer_id != customer_id:
            sample_customer = " from " + existing_sample.customer.internal_id

        message += f" (already existing sample{sample_customer})"
        return message

    @staticmethod
    def add_sample_priority_to_message(message: str, priority: str | None) -> str:
        if priority:
            message += f", priority: {priority}"
        return message

    @staticmethod
    def add_sample_comment_to_message(message: str, comment: str | None) -> str:
        if comment:
            message += f", {comment}"
        return message

    def add_order_comment_to_message(self, message: str, comment: str | None) -> str:
        if comment:
            message += f"{self.NEW_LINE}{comment}."
        return message

    def add_user_name_to_message(self, message: str, name: str | None) -> str:
        if name:
            message += f"{self.NEW_LINE}{name}"
        return message

    def add_customer_to_message(self, message: str, customer_id: str) -> str:
        """Add customer info to message and return updated message."""
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        message += f", {customer.name} ({customer_id})"
        return message

    @classmethod
    def replace_empty_string_with_none(cls, obj: Any) -> Any:
        """Recursive function that replaces empty string in nested dicts/lists with None"""
        if obj == "":
            return None
        if isinstance(obj, dict):
            for key, item in obj.items():
                if isinstance(item, list):
                    processed_list = [
                        cls.replace_empty_string_with_none(list_item) for list_item in item
                    ]
                    obj[key] = processed_list
                else:
                    obj[key] = cls.replace_empty_string_with_none(item)
        return obj

    def connect_to_ticket(
        self, order: OrderIn, user_name: str, user_mail: str, project: str, ticket_number: str
    ) -> None:
        """Appends a new order message to the ticket selected by the customer"""
        LOG.info(f"Connecting order to ticket {ticket_number}")
        message: str = self.add_existing_ticket_header(
            message=self.create_xml_sample_list(order=order, user_name=user_name),
            order=order,
            project=project,
        )
        sender_prefix, email_server_alias = user_mail.split("@")
        temp_dir: TemporaryDirectory = self.osticket.create_connecting_ticket_attachment(
            content=self.replace_empty_string_with_none(obj=order.dict())
        )
        email_form = FormDataRequest(
            sender_prefix=sender_prefix,
            email_server_alias=email_server_alias,
            request_uri=self.osticket.email_uri,
            recipients=self.osticket.osticket_email,
            mail_title=f"[#{ticket_number}]",
            mail_body=message,
            attachments=[Path(f"{temp_dir.name}/order.json")],
        )
        email_form.submit()
        temp_dir.cleanup()

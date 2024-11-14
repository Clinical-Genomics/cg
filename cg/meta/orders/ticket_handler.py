import logging
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.clients.freshdesk.models import ReplyCreate, TicketCreate, TicketResponse
from cg.models.orders.constants import OrderType
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.orders.constants import ORDER_TYPE_WORKFLOW_MAP
from cg.store.models import Customer, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class TicketHandler:
    """Handle tickets in the meta orders context"""

    NEW_LINE = "<br />"

    def __init__(self, db: Store, client: FreshdeskClient, system_email_id: int, env: str):
        self.client: FreshdeskClient = client
        self.status_db: Store = db
        self.system_email_id: int = system_email_id
        self.env: str = env

    @staticmethod
    def parse_ticket_number(name: str) -> str | None:
        """Try to parse a ticket number from a string"""
        # detect manual ticket assignment
        ticket_match = re.fullmatch(r"#(\d{6,10})", name)
        if ticket_match:
            ticket_id = ticket_match.group(1)
            LOG.info(f"{ticket_id}: detected ticket in order name")
            return ticket_id
        LOG.info(f"Could not detected ticket number in name {name}")
        return None

    def create_ticket(
        self, order: Order, user_name: str, user_mail: str, order_type: OrderType
    ) -> int | None:
        """Create a ticket and return the ticket number"""
        message: str = self.create_new_ticket_header(
            message=self.create_xml_sample_list(order=order, user_name=user_name),
            order=order,
            order_type=order_type,
        )

        with TemporaryDirectory() as temp_dir:
            attachments: Path = self.create_attachment_file(order=order, temp_dir=temp_dir)

            freshdesk_ticket = TicketCreate(
                email=user_mail,
                description=message,
                email_config_id=self.system_email_id,
                name=user_name,
                subject=order.name,
                type="Order",
                tags=[ORDER_TYPE_WORKFLOW_MAP[order_type]],
                custom_fields={
                    "cf_environment": self.env,
                },
                attachments=[],
            )
            ticket_response: TicketResponse = self.client.create_ticket(
                ticket=freshdesk_ticket, attachments=[attachments]
            )
            LOG.info(f"{ticket_response.id}: opened new ticket in Freshdesk")

        return ticket_response.id

    def create_attachment_file(self, order: Order, temp_dir: str) -> Path:
        """Create a single attachment file for the ticket"""
        order_file_path = Path(temp_dir) / "order.json"
        with order_file_path.open("w") as order_file:
            order_file.write(order.json())
        return order_file_path

    def create_xml_sample_list(self, order: Order, user_name: str) -> str:
        message = ""
        if isinstance(order, OrderWithCases):
            message = self.create_case_xml_sample_list(order=order, message=message)
        else:
            for sample in order.samples:
                message = self.add_sample_name_to_message(message=message, sample_name=sample.name)
                message = self.add_sample_apptag_to_message(
                    message=message, application=sample.application
                )
                message = self.add_sample_priority_to_message(
                    message=message, priority=sample.priority
                )
                message = self.add_sample_comment_to_message(
                    message=message, comment=sample.comment
                )

        message += self.NEW_LINE
        message = self.add_order_comment_to_message(message=message, comment=order.comment)
        message = self.add_user_name_to_message(message=message, name=user_name)
        message = self.add_customer_to_message(message=message, customer_id=order.customer)

        return message

    @staticmethod
    def create_new_ticket_header(message: str, order: Order, order_type: OrderType) -> str:
        return f"New order with {len(order.samples)} {order_type} samples:" + message

    @staticmethod
    def add_existing_ticket_header(message: str, order: Order, order_type: str) -> str:
        return (
            f"A new order with {len(order.samples)} {order_type} samples has been connected to this ticket:"
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
        self, message: str, customer_id: str, internal_id: str, case_name: str
    ) -> str:

        existing_sample: Sample = self.status_db.get_sample_by_internal_id(internal_id=internal_id)

        sample_customer = ""
        if existing_sample.customer_id != customer_id:
            sample_customer = " from " + existing_sample.customer.internal_id

        message += f"{existing_sample.name}, application: {existing_sample.application_version.application.tag}, case: {case_name} (already existing sample{sample_customer}), priority: {existing_sample.priority}"
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
        self, order: Order, user_name: str, order_type: str, ticket_number: str
    ) -> None:
        """Appends a new order message to the ticket selected by the customer"""
        LOG.info(f"Connecting order to ticket {ticket_number}")

        message: str = self.add_existing_ticket_header(
            message=self.create_xml_sample_list(order=order, user_name=user_name),
            order=order,
            order_type=order_type,
        )

        with TemporaryDirectory() as temp_dir:
            attachments: Path = self.create_attachment_file(order=order, temp_dir=temp_dir)

            reply = ReplyCreate(ticket_number=ticket_number, body=message)

            self.client.reply_to_ticket(
                reply=reply,
                attachments=[attachments],
            )

            LOG.info(f"Connected order to ticket {ticket_number} in Freshdesk")

    def create_case_xml_sample_list(self, order, message: str) -> str:
        for case in order.cases:
            if not case.is_new:
                db_case = self.status_db.get_case_by_internal_id(case.internal_id)
                for sample in db_case.samples:
                    message = self.add_existing_sample_info_to_message(
                        message=message,
                        customer_id=sample.customer.internal_id,
                        internal_id=sample.internal_id,
                        case_name=db_case.name,
                    )
            else:
                for sample in case.samples:
                    if not sample.is_new:
                        message = self.add_existing_sample_info_to_message(
                            message=message,
                            customer_id=order.customer,
                            internal_id=sample.internal_id,
                            case_name=case.name,
                        )
                    else:
                        message = self.add_sample_name_to_message(
                            message=message, sample_name=sample.name
                        )
                        message = self.add_sample_apptag_to_message(
                            message=message, application=sample.application
                        )
                        message = self.add_sample_case_name_to_message(
                            message=message, case_name=case.name
                        )
                        message = self.add_sample_priority_to_message(
                            message=message, priority=sample.priority
                        )
                        message = self.add_sample_comment_to_message(
                            message=message, comment=sample.comment
                        )
        return message

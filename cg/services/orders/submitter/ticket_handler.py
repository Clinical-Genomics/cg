import logging
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.clients.freshdesk.models import TicketCreate, TicketResponse
from cg.constants.priority import Priority
from cg.meta.orders.utils import get_due_by_date, get_ticket_status, get_ticket_tags
from cg.models.orders.constants import OrderType
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.store.models import Case, Customer, Sample
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

    def create_ticket(
        self, order: Order, user_name: str, user_mail: str, order_type: OrderType
    ) -> int | None:
        """Create a ticket and return the ticket number"""
        message: str = self.create_new_ticket_header(
            message=self.create_xml_sample_list(order=order, user_name=user_name),
            order=order,
            order_type=order_type,
        )

        tags: list[str] = get_ticket_tags(
            order=order, order_type=order_type, status_db=self.status_db
        )
        status: int = get_ticket_status(order=order)

        order_priority: Priority = self._get_max_case_priority(order=order)
        deadline_date: date = get_due_by_date(priority=order_priority)

        with TemporaryDirectory() as temp_dir:
            attachments: Path = self.create_attachment_file(order=order, temp_dir=temp_dir)

            freshdesk_ticket = TicketCreate(
                email=user_mail,
                description=message,
                email_config_id=self.system_email_id,
                name=user_name,
                subject=order.name,
                type="Order",
                tags=tags,
                custom_fields={
                    "cf_environment": self.env,
                },
                attachments=[],
                status=status,
                due_by=deadline_date,
                fr_due_by=deadline_date,
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
        nr_samples = (
            len(order.samples)
            if isinstance(order, OrderWithSamples)
            else len(order.enumerated_new_samples)
        )
        return f"New order with {nr_samples} new {order_type} samples:" + message

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
        message += f"{existing_sample.name}, application: {existing_sample.application_version.application.tag}, case: {case_name} (already existing sample{sample_customer}), priority: {existing_sample.priority.name.lower()}"
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

    def create_case_xml_sample_list(self, order, message: str) -> str:
        for case in order.cases:
            if not case.is_new:
                db_case = self.status_db.get_case_by_internal_id(case.internal_id)
                for sample in db_case.samples:
                    message += self.NEW_LINE
                    message = self.add_existing_sample_info_to_message(
                        message=message,
                        customer_id=sample.customer.internal_id,
                        internal_id=sample.internal_id,
                        case_name=db_case.name,
                    )
            else:
                for sample in case.samples:
                    if not sample.is_new:
                        message += self.NEW_LINE
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
                            message=message, priority=case.priority
                        )
                        message = self.add_sample_comment_to_message(
                            message=message, comment=sample.comment
                        )
        return message

    def _get_max_case_priority(self, order: Order) -> Priority:
        """Get max case priority for a given order."""
        priority_list: list[Priority] = []

        if isinstance(order, OrderWithCases):
            for index, new_case in order.enumerated_new_cases:
                priority_list.append(Priority[new_case.priority])

            for index, case in order.enumerated_existing_cases:
                case: Case = self.status_db.get_case_by_internal_id(case.internal_id)
                priority_list.append(case.priority)

        if isinstance(order, OrderWithSamples):
            for sample in order.samples:
                priority_list.append(Priority[sample.priority])

        return max(priority_list)

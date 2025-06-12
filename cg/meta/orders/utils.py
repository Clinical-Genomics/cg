from datetime import date, datetime, timedelta

from cg.clients.freshdesk.constants import Status
from cg.constants.priority import Priority
from cg.models.orders.constants import OrderType
from cg.services.orders.constants import ORDER_TYPE_WORKFLOW_MAP
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.models.sample import Sample as ValidationSample
from cg.store.models import Application, Sample
from cg.store.store import Store

DUE_TIME_BY_PRIORITY: dict[Priority, timedelta] = {
    Priority.express: timedelta(days=7),
    Priority.priority: timedelta(days=14),
    Priority.standard: timedelta(days=21),
    Priority.clinical_trials: timedelta(days=21),
    Priority.research: timedelta(days=60),
}


def contains_existing_data(order: OrderWithCases) -> bool:
    """Check if the order contains any existing data"""
    return any(not case.is_new or case.enumerated_existing_samples for case in order.cases)


def contains_external_data(order: Order, status_db: Store) -> bool:
    """Check if any existing or new sample from the given order is external."""
    existing_samples: list[Sample] = get_existing_samples(order=order, status_db=status_db)
    new_samples: list[ValidationSample] = get_new_samples(order=order)

    if any([sample.is_external for sample in existing_samples]):
        return True

    for sample in new_samples:
        application: Application | None = status_db.get_application_by_tag(sample.application)
        if application and application.is_external:
            return True

    return False


def get_ticket_tags(order: Order, order_type: OrderType, status_db: Store) -> list[str]:
    """Generate ticket tags based on the order and order type"""

    tags: list[str] = [ORDER_TYPE_WORKFLOW_MAP[order_type]]

    if isinstance(order, OrderWithCases):
        if contains_existing_data(order):
            tags.append("existing-data")

    if contains_external_data(order=order, status_db=status_db):
        tags.append("external-data")

    return tags


def contains_only_existing_samples(order: OrderWithCases) -> bool:
    """Check if the order contains only existing samples"""

    if order.enumerated_new_samples:
        return False
    return True


def get_ticket_status(order: Order) -> Status:
    """Get the ticket status based on the order"""

    if isinstance(order, OrderWithCases):
        if contains_only_existing_samples(order=order):
            return Status.OPEN
    return Status.PENDING


def get_due_by_date(priority: Priority) -> date:
    """Get the ticket due by date based on the order priority."""
    due_by: datetime = datetime.now() + DUE_TIME_BY_PRIORITY[priority]
    return due_by.date()


def get_existing_samples(order: Order, status_db: Store) -> list[Sample]:
    existing_samples: list[Sample] = []

    if isinstance(order, OrderWithCases):
        existing_samples.extend(
            [
                sample
                for (_, case) in order.enumerated_existing_cases
                for sample in status_db.get_samples_by_case_id(case.internal_id)
            ]
        )

        existing_samples.extend(
            [
                sample
                for (_, case) in order.enumerated_new_cases
                for (_, existing_sample) in case.enumerated_existing_samples
                if (sample := status_db.get_sample_by_internal_id(existing_sample.internal_id))
            ]
        )

    return existing_samples


def get_new_samples(order: Order) -> list[ValidationSample]:
    new_samples: list[ValidationSample] = []

    if isinstance(order, OrderWithCases):
        new_samples.extend([sample for (_, _, sample) in order.enumerated_new_samples])
    elif isinstance(order, OrderWithSamples):
        new_samples.extend(order.samples)

    return new_samples

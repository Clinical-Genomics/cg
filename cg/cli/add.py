import logging
from typing import List, Optional, Tuple

import click
from cg.constants import PRIORITY_OPTIONS, STATUS_OPTIONS, DataDelivery, Pipeline
from cg.meta.orders.external_data import ExternalDataAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from cg.utils.click.EnumChoice import EnumChoice

LOG = logging.getLogger(__name__)


@click.group()
def add():
    """Add new things to the database."""
    pass


@add.command()
@click.argument("internal_id")
@click.argument("name")
@click.option(
    "-cg",
    "--customer-group",
    "customer_group_id",
    help="internal ID for the customer group of the customer, a new group will be "
    "created if left out",
)
@click.option(
    "-ia",
    "--invoice-address",
    "invoice_address",
    required=True,
    help="Street adress, Post code, City",
)
@click.option(
    "-ir",
    "--invoice-reference",
    "invoice_reference",
    required=True,
    help="Invoice reference (text)",
)
@click.pass_obj
def customer(
    context: CGConfig,
    internal_id: str,
    name: str,
    customer_group_id: Optional[str],
    invoice_address: str,
    invoice_reference: str,
):
    """Add a new customer with a unique INTERNAL_ID and NAME."""
    status_db: Store = context.status_db
    existing: models.Customer = status_db.customer(internal_id)
    if existing:
        LOG.error(f"{existing.name}: customer already added")
        raise click.Abort

    customer_group: models.CustomerGroup = status_db.customer_group(customer_group_id)
    if not customer_group:
        customer_group: models.CustomerGroup = status_db.add_customer_group(
            internal_id=internal_id, name=name
        )

    new_customer: models.Customer = status_db.add_customer(
        internal_id=internal_id,
        name=name,
        customer_group=customer_group,
        invoice_address=invoice_address,
        invoice_reference=invoice_reference,
    )
    status_db.add_commit(new_customer)
    message: str = f"customer added: {new_customer.internal_id} ({new_customer.id})"
    LOG.info(message)


@add.command()
@click.option("-a", "--admin", is_flag=True, help="make the user an admin")
@click.option(
    "-c",
    "--customer",
    "customer_id",
    required=True,
    help="internal ID for the customer of the user",
)
@click.argument("email")
@click.argument("name")
@click.pass_obj
def user(context: CGConfig, admin: bool, customer_id: str, email: str, name: str):
    """Add a new user with an EMAIL (login) and a NAME (full)."""
    status_db: Store = context.status_db
    customer_obj: models.Customer = status_db.customer(customer_id)
    existing: models.User = status_db.user(email)
    if existing:
        LOG.error(f"{existing.name}: user already added")
        raise click.Abort
    new_user: models.User = status_db.add_user(
        customer=customer_obj, email=email, name=name, is_admin=admin
    )
    status_db.add_commit(new_user)
    LOG.info(f"user added: {new_user.email} ({new_user.id})")


@add.command()
@click.option("-l", "--lims", "lims_id", help="LIMS id for the sample")
@click.option("-d", "--downsampled", type=int, help="how many reads is the sample downsampled to?")
@click.option("-o", "--order", help="name of the order the sample belongs to")
@click.option(
    "-s",
    "--sex",
    type=click.Choice(["male", "female", "unknown"]),
    required=True,
    help="sample pedigree sex",
)
@click.option("-a", "--application", required=True, help="application tag name")
@click.option(
    "-p",
    "--priority",
    type=click.Choice(PRIORITY_OPTIONS),
    default="standard",
    help="set the priority for the samples",
)
@click.argument("customer_id")
@click.argument("name")
@click.pass_obj
def sample(
    context: CGConfig,
    lims_id: Optional[str],
    downsampled: Optional[int],
    sex: str,
    order: Optional[str],
    application: str,
    priority: str,
    customer_id: str,
    name: str,
):
    """Add a sample for CUSTOMER_ID with a NAME (display)."""
    status_db: Store = context.status_db
    customer_obj: models.Customer = status_db.customer(customer_id)
    if customer_obj is None:
        LOG.error("customer not found")
        raise click.Abort
    application_obj: models.Application = status_db.application(application)
    if application_obj is None:
        LOG.error("application not found")
        raise click.Abort
    new_record: models.Sample = status_db.add_sample(
        name=name,
        sex=sex,
        internal_id=lims_id,
        order=order,
        downsampled_to=downsampled,
        priority=priority,
    )
    new_record.application_version = status_db.current_application_version(application)
    new_record.customer = customer_obj
    status_db.add_commit(new_record)
    LOG.info(f"{new_record.internal_id}: new sample added")


@add.command()
@click.option(
    "--priority", type=click.Choice(PRIORITY_OPTIONS), default="standard", help="analysis priority"
)
@click.option("-p", "--panel", "panels", multiple=True, help="default gene panels")
@click.option(
    "-a",
    "--analysis",
    "data_analysis",
    help="Analysis workflow",
    required=True,
    type=EnumChoice(Pipeline),
)
@click.option(
    "-dd",
    "--data-delivery",
    "data_delivery",
    help="Update case data delivery",
    required=True,
    type=EnumChoice(DataDelivery),
)
@click.argument("customer_id")
@click.argument("name")
@click.pass_obj
def family(
    context: CGConfig,
    priority: str,
    panels: Tuple[str],
    data_analysis: Pipeline,
    data_delivery: DataDelivery,
    customer_id: str,
    name: str,
):
    """Add a family to CUSTOMER_ID with a NAME."""
    status_db: Store = context.status_db
    customer_obj: models.Customer = status_db.customer(customer_id)
    if customer_obj is None:
        LOG.error(f"{customer_id}: customer not found")
        raise click.Abort

    for panel_id in panels:
        panel_obj: models.Panel = status_db.panel(panel_id)
        if panel_obj is None:
            LOG.error(f"{panel_id}: panel not found")
            raise click.Abort

    new_case: models.Family = status_db.add_case(
        data_analysis=data_analysis,
        data_delivery=data_delivery,
        name=name,
        panels=list(panels),
        priority=priority,
    )
    new_case.customer = customer_obj
    status_db.add_commit(new_case)
    LOG.info(f"{new_case.internal_id}: new case added")


@add.command()
@click.option("-m", "--mother", help="sample ID for mother of sample")
@click.option("-f", "--father", help="sample ID for father of sample")
@click.option("-s", "--status", type=click.Choice(STATUS_OPTIONS), required=True)
@click.argument("family_id")
@click.argument("sample_id")
@click.pass_obj
def relationship(
    context: CGConfig,
    mother: Optional[str],
    father: Optional[str],
    status: str,
    family_id: str,
    sample_id: str,
):
    """Create a link between a FAMILY_ID and a SAMPLE_ID."""
    status_db: Store = context.status_db
    mother_obj: Optional[models.Sample] = None
    father_obj: Optional[models.Sample] = None
    case_obj: models.Family = status_db.family(family_id)
    if case_obj is None:
        LOG.error("%s: family not found", family_id)
        raise click.Abort

    sample_obj: models.Sample = status_db.sample(sample_id)
    if sample_obj is None:
        LOG.error("%s: sample not found", sample_id)
        raise click.Abort

    if mother:
        mother_obj: models.Sample = status_db.sample(mother)
        if mother_obj is None:
            LOG.error("%s: mother not found", mother)
            raise click.Abort

    if father:
        father_obj: models.Sample = status_db.sample(father)
        if father_obj is None:
            LOG.error("%s: father not found", father)
            raise click.Abort

    new_record = status_db.relate_sample(
        family=case_obj, sample=sample_obj, status=status, mother=mother_obj, father=father_obj
    )
    status_db.add_commit(new_record)
    LOG.info("related %s to %s", case_obj.internal_id, sample_obj.internal_id)


@add.command()
@click.option(
    "-t",
    "--ticket-id",
    type=int,
    help="Ticket id",
    required=True,
)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def external(context: CGConfig, ticket_id: int, dry_run: bool):
    """Downloads external data from caesar and places it in appropriate folder on hasta"""
    external_data_api = ExternalDataAPI(config=context)
    external_data_api.download_ticket(ticket_id=ticket_id, dry_run=dry_run)


@add.command("external-hk")
@click.option(
    "-t",
    "--ticket-id",
    type=int,
    help="Ticket id",
    required=True,
)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def external_hk(context: CGConfig, ticket_id: int, dry_run: bool):
    """Adds external data to housekeeper"""
    external_data_api = ExternalDataAPI(config=context)
    external_data_api.configure_housekeeper(ticket_id=ticket_id, dry_run=dry_run)

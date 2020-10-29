import logging
import click

from cg.constants import PRIORITY_OPTIONS, STATUS_OPTIONS
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def add(context):
    """Add new things to the database."""
    context.obj["status_db"] = Store(context.obj["database"])


@add.command()
@click.argument("internal_id")
@click.argument("name")
@click.option(
    "-cg",
    "--customer-group",
    "customer_group_id",
    required=False,
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
@click.pass_context
def customer(
    context,
    internal_id: str,
    name: str,
    customer_group_id: str,
    invoice_address: str,
    invoice_reference: str,
):
    """Add a new customer with a unique INTERNAL_ID and NAME."""
    existing = context.obj["status_db"].customer(internal_id)
    if existing:
        LOG.error(f"{existing.name}: customer already added")
        context.abort()

    customer_group = context.obj["status_db"].customer_group(customer_group_id)
    if not customer_group:
        customer_group = context.obj["status_db"].add_customer_group(
            internal_id=internal_id, name=name
        )

    new_customer = context.obj["status_db"].add_customer(
        internal_id=internal_id,
        name=name,
        customer_group=customer_group,
        invoice_address=invoice_address,
        invoice_reference=invoice_reference,
    )
    context.obj["status_db"].add_commit(new_customer)
    message = f"customer added: {new_customer.internal_id} ({new_customer.id})"
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
@click.pass_context
def user(context, admin, customer_id, email, name):
    """Add a new user with an EMAIL (login) and a NAME (full)."""
    customer_obj = context.obj["status_db"].customer(customer_id)
    existing = context.obj["status_db"].user(email)
    if existing:
        LOG.error(f"{existing.name}: user already added")
        context.abort()
    new_user = context.obj["status_db"].add_user(customer_obj, email, name, is_admin=admin)
    context.obj["status_db"].add_commit(new_user)
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
@click.pass_context
def sample(context, lims_id, downsampled, sex, order, application, priority, customer_id, name):
    """Add a sample for CUSTOMER_ID with a NAME (display)."""
    status = context.obj["status_db"]
    customer_obj = status.customer(customer_id)
    if customer_obj is None:
        LOG.error("customer not found")
        context.abort()
    application_obj = status.application(application)
    if application_obj is None:
        LOG.error("application not found")
        context.abort()
    new_record = status.add_sample(
        name=name,
        sex=sex,
        internal_id=lims_id,
        order=order,
        downsampled_to=downsampled,
        priority=priority,
    )
    new_record.application_version = status.current_application_version(application)
    new_record.customer = customer_obj
    status.add_commit(new_record)
    LOG.info(f"{new_record.internal_id}: new sample added")


@add.command()
@click.option(
    "--priority", type=click.Choice(PRIORITY_OPTIONS), default="standard", help="analysis priority"
)
@click.option("-p", "--panel", "panels", multiple=True, required=True, help="default gene panels")
@click.option("-a", "--analysis", required=True, help="Analysis workflow")
@click.argument("customer_id")
@click.argument("name")
@click.pass_context
def family(context, priority, panels, analysis, customer_id, name):
    """Add a family to CUSTOMER_ID with a NAME."""
    status = context.obj["status_db"]
    customer_obj = status.customer(customer_id)
    if customer_obj is None:
        LOG.error(f"{customer_id}: customer not found")
        context.abort()

    for panel_id in panels:
        panel_obj = status.panel(panel_id)
        if panel_obj is None:
            LOG.error(f"{panel_id}: panel not found")
            context.abort()

    new_family = status.add_family(
        data_analysis=analysis, name=name, panels=panels, priority=priority
    )
    new_family.customer = customer_obj
    status.add_commit(new_family)
    LOG.info(f"{new_family.internal_id}: new family added")


@add.command()
@click.option("-m", "--mother", help="sample ID for mother of sample")
@click.option("-f", "--father", help="sample ID for father of sample")
@click.option("-s", "--status", type=click.Choice(STATUS_OPTIONS), required=True)
@click.argument("family_id")
@click.argument("sample_id")
@click.pass_context
def relationship(context, mother, father, status, family_id, sample_id):
    """Create a link between a FAMILY_ID and a SAMPLE_ID."""
    status_db = context.obj["status_db"]
    mother_obj = None
    father_obj = None
    family_obj = status_db.family(family_id)
    if family_obj is None:
        LOG.error("%s: family not found", family_id)
        context.abort()

    sample_obj = status_db.sample(sample_id)
    if sample_obj is None:
        LOG.error("%s: sample not found", sample_id)
        context.abort()

    if mother:
        mother_obj = status_db.sample(mother)
        if mother_obj is None:
            LOG.error("%s: mother not found", mother)
            context.abort()

    if father:
        father_obj = status_db.sample(father)
        if father_obj is None:
            LOG.error("%s: father not found", father)
            context.abort()

    new_record = status_db.relate_sample(
        family_obj, sample_obj, status, mother=mother_obj, father=father_obj
    )
    status_db.add_commit(new_record)
    LOG.info(f"related {family_obj.internal_id} to {sample_obj.internal_id}")

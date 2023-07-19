import logging
from typing import List, Optional, Tuple

import click
from cg.constants import STATUS_OPTIONS, DataDelivery, Pipeline, Priority
from cg.constants.subject import Gender
from cg.meta.transfer.external_data import ExternalDataAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import (
    Application,
    ApplicationVersion,
    Collaboration,
    Customer,
    Family,
    FamilySample,
    Panel,
    Sample,
    User,
)
from cg.utils.click.EnumChoice import EnumChoice

LOG = logging.getLogger(__name__)


@click.group()
def add():
    """Add new things to the database."""
    pass


@add.command("customer")
@click.argument("internal_id")
@click.argument("name")
@click.option(
    "-cg",
    "--collaboration-internal-ids",
    "collaboration_internal_ids",
    multiple=True,
    help="List of internal IDs for the collaborations the customer should belong to",
)
@click.option(
    "-ia",
    "--invoice-address",
    "invoice_address",
    required=True,
    help="Street address, Post code, City",
)
@click.option(
    "-ir",
    "--invoice-reference",
    "invoice_reference",
    required=True,
    help="Invoice reference (text)",
)
@click.option(
    "-da",
    "--data-archive-location",
    "data_archive_location",
    help="Specifies where to store data for the customer.",
    default="PDC",
    show_default=True,
    required=False,
)
@click.option(
    "-ic",
    "--is-clinical",
    "is_clinical",
    help="Set to true to indicate that this customer is clinical"
    " and handle data storage accordingly, i.e. for 10 years instead if 2 years.",
    is_flag=True,
    default=False,
    show_default=True,
    required=False,
)
@click.pass_obj
def add_customer(
    context: CGConfig,
    internal_id: str,
    name: str,
    collaboration_internal_ids: Optional[List[str]],
    invoice_address: str,
    invoice_reference: str,
    data_archive_location: str,
    is_clinical: bool,
):
    """Add a new customer with a unique internal id and name."""
    collaboration_internal_ids = collaboration_internal_ids or []
    status_db: Store = context.status_db

    existing_customer: Customer = status_db.get_customer_by_internal_id(
        customer_internal_id=internal_id
    )
    if existing_customer:
        LOG.error(f"{existing_customer.name}: customer already added")
        raise click.Abort

    collaborations: List[Collaboration] = [
        status_db.get_collaboration_by_internal_id(internal_id=collaboration_internal_id)
        for collaboration_internal_id in collaboration_internal_ids
    ]

    new_customer: Customer = status_db.add_customer(
        internal_id=internal_id,
        name=name,
        invoice_address=invoice_address,
        invoice_reference=invoice_reference,
        data_archive_location=data_archive_location,
        is_clinical=is_clinical,
    )
    for collaboration in collaborations:
        new_customer.collaborations.append(collaboration)
    status_db.session.add(new_customer)
    status_db.session.commit()
    message: str = f"customer added: {new_customer.internal_id} ({new_customer.id})"
    LOG.info(message)


@add.command("user")
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
def add_user(context: CGConfig, admin: bool, customer_id: str, email: str, name: str):
    """Add a new user with an EMAIL (login) and a NAME (full)."""
    status_db: Store = context.status_db

    customer_obj: Customer = status_db.get_customer_by_internal_id(customer_internal_id=customer_id)
    existing_user: User = status_db.get_user_by_email(email=email)
    if existing_user:
        LOG.error(f"{existing_user.name}: user already added")
        raise click.Abort

    new_user: User = status_db.add_user(
        customer=customer_obj, email=email, name=name, is_admin=admin
    )
    status_db.session.add(new_user)
    status_db.session.commit()
    LOG.info(f"User added: {new_user.email} ({new_user.id})")


@add.command("sample")
@click.option("-l", "--lims", "lims_id", help="LIMS id for the sample")
@click.option(
    "-d", "--down-sampled", type=int, help="How many reads is the sample down sampled to?"
)
@click.option("-o", "--order", help="Name of the order the sample belongs to")
@click.option(
    "-s",
    "--sex",
    type=EnumChoice(Gender, use_value=False),
    required=True,
    help="Sample pedigree sex",
)
@click.option("-a", "--application-tag", required=True, help="application tag name")
@click.option(
    "-p",
    "--priority",
    type=EnumChoice(Priority, use_value=False),
    default="standard",
    help="Set the priority for the samples",
)
@click.argument("customer_id")
@click.argument("name")
@click.pass_obj
def add_sample(
    context: CGConfig,
    lims_id: Optional[str],
    down_sampled: Optional[int],
    sex: Gender,
    order: Optional[str],
    application_tag: str,
    priority: Priority,
    customer_id: str,
    name: str,
):
    """Add a sample for CUSTOMER_ID with a NAME (display)."""
    status_db: Store = context.status_db

    customer: Customer = status_db.get_customer_by_internal_id(customer_internal_id=customer_id)
    if not customer:
        LOG.error(f"Customer: {customer_id} not found")
        raise click.Abort
    application: Application = status_db.get_application_by_tag(tag=application_tag)
    if not application:
        LOG.error(f"Application: {application_tag} not found")

        raise click.Abort
    new_record: Sample = status_db.add_sample(
        name=name,
        sex=sex,
        downsampled_to=down_sampled,
        internal_id=lims_id,
        order=order,
        priority=priority,
    )
    new_record.application_version: ApplicationVersion = (
        status_db.get_current_application_version_by_tag(tag=application_tag)
    )
    new_record.customer: Customer = customer
    status_db.session.add(new_record)
    status_db.session.commit()
    LOG.info(f"{new_record.internal_id}: new sample added")


@add.command("case")
@click.option(
    "--priority",
    type=EnumChoice(Priority, use_value=False),
    default="standard",
    help="analysis priority",
)
@click.option("-p", "--panel", "panel_abbreviations", multiple=True, help="default gene panels")
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
@click.option("-t", "--ticket", help="Ticket number", required=True)
@click.argument("customer_id")
@click.argument("name")
@click.pass_obj
def add_case(
    context: CGConfig,
    priority: Priority,
    panel_abbreviations: Tuple[str],
    data_analysis: Pipeline,
    data_delivery: DataDelivery,
    customer_id: str,
    name: str,
    ticket: str,
):
    """Add a case with the given name and associated with the given customer"""
    status_db: Store = context.status_db

    customer: Customer = status_db.get_customer_by_internal_id(customer_internal_id=customer_id)
    if customer is None:
        LOG.error(f"{customer_id}: customer not found")
        raise click.Abort

    for panel_abbreviation in panel_abbreviations:
        panel: Panel = status_db.get_panel_by_abbreviation(abbreviation=panel_abbreviation)

        if panel is None:
            LOG.error(f"{panel_abbreviation}: panel not found")
            raise click.Abort

    new_case: Family = status_db.add_case(
        data_analysis=data_analysis,
        data_delivery=data_delivery,
        name=name,
        panels=list(panel_abbreviations),
        priority=priority,
        ticket=ticket,
    )

    new_case.customer: Customer = customer
    status_db.session.add(new_case)
    status_db.session.commit()
    LOG.info(f"{new_case.internal_id}: new case added")


@add.command("relationship")
@click.option("-m", "--mother-id", help="Sample ID for mother of sample")
@click.option("-f", "--father-id", help="Sample ID for father of sample")
@click.option("-s", "--status", type=click.Choice(STATUS_OPTIONS), required=True)
@click.argument("case-id")
@click.argument("sample-id")
@click.pass_obj
def link_sample_to_case(
    context: CGConfig,
    mother_id: Optional[str],
    father_id: Optional[str],
    status: str,
    case_id: str,
    sample_id: str,
):
    """Create a link between a case id and a sample id."""
    status_db: Store = context.status_db
    mother: Optional[Sample] = None
    father: Optional[Sample] = None
    case_obj: Family = status_db.get_case_by_internal_id(internal_id=case_id)
    if case_obj is None:
        LOG.error("%s: family not found", case_id)
        raise click.Abort

    sample: Sample = status_db.get_sample_by_internal_id(internal_id=sample_id)
    if sample is None:
        LOG.error("%s: sample not found", sample_id)
        raise click.Abort

    if mother_id:
        mother: Sample = status_db.get_sample_by_internal_id(internal_id=mother_id)
        if mother is None:
            LOG.error("%s: mother not found", mother_id)
            raise click.Abort

    if father_id:
        father: Sample = status_db.get_sample_by_internal_id(internal_id=father_id)
        if father is None:
            LOG.error("%s: father not found", father_id)
            raise click.Abort

    new_record: FamilySample = status_db.relate_sample(
        family=case_obj, sample=sample, status=status, mother=mother, father=father
    )
    status_db.session.add(new_record)
    status_db.session.commit()
    LOG.info("related %s to %s", case_obj.internal_id, sample.internal_id)


@add.command("external")
@click.option(
    "-t",
    "--ticket",
    type=str,
    help="Ticket id",
    required=True,
)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def download_external_delivery_data_to_hpc(context: CGConfig, ticket: str, dry_run: bool):
    """Downloads external data from the delivery server and places it in appropriate folder on
    the HPC"""
    external_data_api = ExternalDataAPI(config=context)
    external_data_api.transfer_sample_files_from_source(ticket=ticket, dry_run=dry_run)


@add.command("external-hk")
@click.option(
    "-t",
    "--ticket",
    type=str,
    help="Ticket id",
    required=True,
)
@click.option("--dry-run", is_flag=True)
@click.option(
    "--force", help="Overwrites any any previous samples in the customer directory", is_flag=True
)
@click.pass_obj
def add_external_data_to_hk(context: CGConfig, ticket: str, dry_run: bool, force):
    """Adds external data to Housekeeper"""
    external_data_api = ExternalDataAPI(config=context)
    external_data_api.add_transfer_to_housekeeper(dry_run=dry_run, ticket=ticket, force=force)

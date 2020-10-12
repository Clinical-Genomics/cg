import click
from .family import family
from cg.constants import FAMILY_ACTIONS, PRIORITY_OPTIONS
from cg.store import models, Store

CONFIRM = "Continue?"


def _get_samples_by_identifiers(
    identifiers: click.Tuple([str, str]), store: Store
) -> [models.Sample]:
    """Get samples matched by given set of identifiers"""
    identifier_args = {}
    for identifier_name, identifier_value in identifiers:
        identifier_args[identifier_name] = identifier_value
    return store.samples_by_ids(**identifier_args)


def _get_cases(identifiers: click.Tuple([str, str]), store: Store) -> [models.Family]:
    """Get cases that have samples that match identifiers if given"""
    samples_by_id = _get_samples_by_identifiers(identifiers, store)
    cases = set()
    for sample in samples_by_id:

        for link in sample.links:
            cases.add(link.family)

    return cases


@click.command()
@click.option(
    "--sample-identifier",
    "identifiers",
    nargs=2,
    type=click.Tuple([str, str]),
    multiple=True,
    help="Give an identifier on sample and the value to use it with, e.g. -id name Prov52",
)
@click.option("-a", "--action", type=click.Choice(FAMILY_ACTIONS), help="update family action")
@click.option("-c", "--customer-id", type=click.STRING, help="update customer")
@click.option("-g", "--panel", "panels", multiple=True, help="update gene panels")
@click.option("-p", "--priority", type=click.Choice(PRIORITY_OPTIONS), help="update priority")
@click.pass_context
def families(
    context: click.Context,
    action,
    priority,
    panels,
    customer_id,
    identifiers: click.Tuple([str, str]),
):
    """Set values on many samples at the same time"""
    store = context.obj["status"]
    cases = _get_cases(identifiers, store)

    if not cases:
        click.echo(click.style(fg="red", text="No cases to alter!"))
        context.abort()

    click.echo("Would alter cases:")

    for case in cases:
        click.echo(f"{case}")

    if not (click.confirm(CONFIRM)):
        context.abort()

    for case in cases:
        context.invoke(
            family,
            action=action,
            priority=priority,
            panels=panels,
            family_id=case.internal_id,
            customer_id=customer_id,
        )

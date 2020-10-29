import logging

import click
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group("reset")
@click.pass_context
def reset_cmd(context):
    """Reset information in the database."""
    context.obj["status_db"] = Store(context.obj["database"])


@reset_cmd.command()
@click.option("-c", "--case_id", help="internal case id, leave empty to process all")
@click.pass_context
def observations(context, case_id):
    """Reset observation links from an analysis to LoqusDB."""

    if case_id:
        observations_uploaded = [context.obj["status_db"].family(case_id)]
    else:
        observations_uploaded = context.obj["status_db"].observations_uploaded()

    for family_obj in observations_uploaded:
        LOG.info("This would reset observation links for: %s", family_obj.internal_id)

    click.confirm("Do you want to continue?", abort=True)

    for family_obj in observations_uploaded:
        context.obj["status_db"].reset_observations(family_obj.internal_id)
        LOG.info("Reset loqus observations for: %s", family_obj.internal_id)

    context.obj["status_db"].commit()

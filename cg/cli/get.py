import re
import click

from cg.store import Store


@click.group(invoke_without_command=True)
@click.argument('identifier', required=False)
@click.pass_context
def get(context, identifier):
    """Get information about records in the database."""
    context.obj['status'] = Store(context.obj['database'])
    if identifier and re.match(r'[A-Z]{3}[0-9]{4,5}[A-Z]{1}[1-9]{1,3}', identifier):
        context.invoke(sample, sample_id=identifier)
    elif identifier and re.match(r'^[A-Z]*$', identifier):
        # try family information
        context.invoke(family, family_id=identifier)
    else:
        click.echo(click.style("can't predict identifier", fg='yellow'))


@get.command()
@click.pass_context
def sample(context, sample_id):
    """Get information about a sample."""
    sample_obj = context.obj['status'].sample(sample_id)
    if sample_obj is None:
        click.echo(click.style(f"sample doesn't exist: {sample_id}", fg='red'))
        context.abort()
    message = (f"{sample_obj.internal_id} ({sample_obj.name}) | "
               f"{sample_obj.customer.internal_id} | "
               f"{sample_obj.application_version.application.tag} | [{sample_obj.state}]")
    if sample_obj.priority_human != 'standard':
        message = f"{message} - {sample_obj.priority_human.upper()}"
    if sample_obj.is_external:
        message = f"{message} - EXTERNAL"
    click.echo(message)


@get.command()
@click.pass_context
def family(context, family_id):
    """Get information about a family."""
    family_obj = context.obj['status'].family(family_id)
    if family_obj is None:
        click.echo(click.style(f"family doesn't exist: {family_id}", fg='red'))
        context.abort()
    message = (f"{family_obj.internal_id} ({family_obj.name}) | "
               f"{family_obj.customer.internal_id}")
    if family_obj.priority_human != 'standard':
        message = f"{message} - {family_obj.priority_human.upper()}"
    if family_obj.action:
        message = f"{message} - [{family_obj.action}]"
    click.echo(message)
    for link_obj in family.links:
        context.invoke(sample, sample_id=link_obj.sample.internal_id)

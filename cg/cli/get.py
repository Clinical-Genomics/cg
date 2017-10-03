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
    if sample_obj.priority != 'standard':
        message = f"{message} - {sample_obj.priority.upper()}"
    if sample_obj.is_external:
        message = f"{message} - EXTERNAL"

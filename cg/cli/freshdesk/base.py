import click

from cg.apps.freshdesk.freshdesk_api import Freshdesk

# TODO: Add Keys to CG config
# from freshdesk.keys import FRESHDESK_API_KEY, FRESHDESK_DOMAIN


API_KEY = "YOUR_API_KEY"
DOMAIN = "scilifelab.freshdesk.com"
freshdesk = Freshdesk(api_key=API_KEY, domain=DOMAIN)


@click.group()
def freshdesk_cli():
    """CLI for interacting with Freshdesk."""
    pass


@freshdesk_cli.command()
@click.argument("ticket_id", type=int)
@click.option("--verbose", is_flag=True, help="Show detailed output.")
def get_ticket(ticket_id, verbose):
    """Retrieve details of a ticket."""
    try:
        ticket = Freshdesk.get_ticket(ticket_id, verbose=verbose)
        click.echo(ticket)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@freshdesk_cli.command()
@click.argument("ticket_id", type=int)
@click.argument("message", type=str)
@click.option(
    "--private/--public", default=True, help="Set the message visibility (default: private)."
)
@click.option("--verbose", is_flag=True, help="Show detailed output.")
def post_message(ticket_id, message, private, verbose):
    """Post a html message to a ticket."""
    try:
        response = Freshdesk.post_ticket_message(ticket_id, message, private, verbose=verbose)
        click.echo(f"Message posted: {response}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@freshdesk_cli.command()
@click.argument("ticket_id", type=int)
@click.argument("status", type=int)
@click.option("--verbose", is_flag=True, help="Show detailed output.")
def set_status(ticket_id, status, verbose):
    """
    Update the status of a ticket.
    \n
                2: "Open",\n
                3: "Pending",\n
                4: "Resolved",\n
                5: "Closed"\n
    """
    try:
        # TODO: Use response
        Freshdesk.set_ticket_status(ticket_id, status, verbose=verbose)
        click.echo(f"Ticket {ticket_id} status updated to {status}.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@freshdesk_cli.command()
@click.argument("ticket_id", type=int)
@click.option("--verbose", is_flag=True, help="Show detailed output.")
def get_tags(ticket_id, verbose):
    """Retrieve tags of a ticket."""
    try:
        tags = Freshdesk.get_ticket_tags(ticket_id)
        click.echo(f"Tags: {tags}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@freshdesk_cli.command()
@click.argument("ticket_id", type=int)
@click.option("--verbose", is_flag=True, help="Show detailed output.")
def get_group(ticket_id, verbose):
    """Retrieve group assigned to a ticket."""
    try:
        group_id = Freshdesk.get_ticket_group(ticket_id)
        if verbose:
            # TODO: Add this to a utils function
            group_id_mapping = {
                None: "Unassigned",
                202000118168: "Production Bioinformatics",
                202000118167: "Production Lab",
                202000118169: "Production Managers",
            }
            click.echo(f"group_id: {group_id_mapping[group_id]}")
        else:
            click.echo(f"group_id: {group_id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@freshdesk_cli.command()
@click.argument("ticket_id", type=int, required=True)
@click.argument("group_id", type=int, required=True)
@click.option("--verbose", is_flag=True, help="Show detailed output.")
def set_group(ticket_id, group_id, verbose):
    """Assign a group to a ticket.\n
    202000118168: "Production Bioinformatics",\n
    202000118167: "Production Lab",\n
    202000118169: "Production Managers"\n

    """
    try:
        group_assigned = Freshdesk.set_ticket_group(ticket_id, group_id)
        if verbose:
            # TODO: Add this to a utils function
            group_id_mapping = {
                None: "Unassigned",
                202000118168: "Production Bioinformatics",
                202000118167: "Production Lab",
                202000118169: "Production Managers",
            }
            click.echo(f"group_id: {group_id_mapping[group_assigned]}")
        else:
            click.echo(f"group_id: {group_assigned}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@freshdesk_cli.command()
@click.argument("ticket_id", type=int)
@click.argument("tag", type=str)
@click.option("--verbose", is_flag=True, help="Show detailed output.")
def add_tag(ticket_id, tag, verbose):
    """Add a tag to a ticket."""
    try:
        # TODO: Use the response
        Freshdesk.add_ticket_tag(ticket_id, tag, verbose=verbose)
        click.echo(f"Tag '{tag}' added to ticket {ticket_id}.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@freshdesk_cli.command()
@click.argument("ticket_id", type=int)
@click.argument("tag", type=str)
@click.option("--verbose", is_flag=True, help="Show detailed output.")
def remove_tag(ticket_id, tag, verbose):
    """Remove a tag from a ticket."""
    try:
        # TODO: Use the response
        Freshdesk.remove_ticket_tag(ticket_id, tag, verbose=verbose)
        click.echo(f"Tag '{tag}' removed from ticket {ticket_id}.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@freshdesk_cli.command()
@click.argument("ticket_id", type=int)
@click.option("--verbose", is_flag=True, help="Show detailed output.")
def get_status(ticket_id, verbose):
    """Retrieve the status of a ticket.
    \n
            2: "Open",\n
            3: "Pending",\n
            4: "Resolved",\n
            5: "Closed"\n
    """
    try:
        status = Freshdesk.get_ticket_status(ticket_id)
        if verbose:
            # TODO: Add this to a utils function
            status_mapping = {2: "Open", 3: "Pending", 4: "Resolved", 5: "Closed"}
            click.echo(
                f"Ticket {ticket_id} status: {status_mapping.get(status, 'Unknown')} ({status})"
            )
        else:
            click.echo(status)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

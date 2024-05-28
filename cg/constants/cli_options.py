import click

DRY_RUN = click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Runs the command without making any changes",
)

SKIP_CONFIRMATION = click.option(
    "-y",
    "--yes",
    is_flag=True,
    default=False,
    help="Skip confirmation",
)

FORCE = click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Override any warnings or confirmation prompts",
)

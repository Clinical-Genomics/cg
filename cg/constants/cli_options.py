import rich_click as click

DRY_RUN = click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Runs the command without making any changes",
)

SKIP_CONFIRMATION = click.option(
    "-y",
    "--skip-confirmation",
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

COMMENT = click.option(
    "--comment",
    type=str,
    required=False,
    help="A comment providing an explanation for the forced action",
)

LIMIT = click.option(
    "--limit",
    type=int,
    help="Maximum number of cases to start",
)

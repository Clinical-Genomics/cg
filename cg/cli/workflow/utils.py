"""CLI utility methods."""

import rich_click as click


def validate_force_store_option(force: bool, comment: str | None):
    """Validate that the --comment option is provided when --force is set."""
    if force and not comment:
        raise click.UsageError("The --comment option is required when --force is used")

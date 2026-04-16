import rich_click as click

OPTION_PANEL_BED = click.option(
    "--panel-bed",
    required=False,
    help="Panel BED is determined based on capture kit \
    used for library prep. Set this option to override the default",
)
OPTION_WORKFLOW_PROFILE = click.option(
    "--workflow-profile",
    type=click.Path(exists=True),
    required=False,
    help="Path to directory containing config.yaml.",
)

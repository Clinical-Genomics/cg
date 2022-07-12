"""CLI support for nextflow pipelines """


import click


OPTION_GENDER = click.option(
    "--gender",
    type=click.Choice([Gender.FEMALE, Gender.MALE]),
    required=False,
    help="Case associated gender. Set this option to override the one selected by the customer in StatusDB.",
)


"""Code for validating an upload via CLI"""

import click

from cg.apps.coverage import ChanjoAPI

from .utils import suggest_cases_to_upload


@click.command()
@click.argument("family_id", required=False)
@click.pass_context
def validate(context, family_id):
    """Validate a family of samples."""

    click.echo(click.style("----------------- VALIDATE --------------------"))

    if not family_id:
        suggest_cases_to_upload(context)
        context.abort()

    family_obj = context.obj["status_db"].family(family_id)
    chanjo_api = ChanjoAPI(context.obj)
    chanjo_samples = []
    for link_obj in family_obj.links:
        sample_id = link_obj.sample.internal_id
        chanjo_sample = chanjo_api.sample(sample_id)
        if chanjo_sample is None:
            click.echo(click.style(f"upload coverage for {sample_id}", fg="yellow"))
            continue
        chanjo_samples.append(chanjo_sample)

    if not chanjo_samples:
        return

    coverage_results = chanjo_api.omim_coverage(chanjo_samples)
    for link_obj in family_obj.links:
        sample_id = link_obj.sample.internal_id
        if sample_id in coverage_results:
            completeness = coverage_results[sample_id]["mean_completeness"]
            mean_coverage = coverage_results[sample_id]["mean_coverage"]
            click.echo(f"{sample_id}: {mean_coverage:.2f}X - {completeness:.2f}%")
        else:
            click.echo(f"{sample_id}: sample not found in chanjo", color="yellow")

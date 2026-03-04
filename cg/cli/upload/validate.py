"""Code for validating an upload via CLI"""

from typing import cast

import rich_click as click

from cg.apps.coverage.api import ChanjoAPI
from cg.models.cg_config import CGConfig, ChanjoConfig
from cg.store.store import Store

from .utils import suggest_cases_to_upload


@click.command()
@click.argument("family_id", required=False)
@click.option(
    "--genome-version",
    type=click.Choice(["hg19", "hg38"]),
    default="hg19",
    help="Which chanjo instance to validate against",
)
@click.pass_obj
def validate(context: CGConfig, family_id: str | None, genome_version: str):
    """Validate a family of samples."""

    status_db: Store = context.status_db
    chanjo_config = cast(
        ChanjoConfig, context.chanjo_38 if genome_version == "hg38" else context.chanjo
    )
    chanjo_api = ChanjoAPI(config=chanjo_config)

    click.echo(click.style("----------------- VALIDATE --------------------"))

    if not family_id:
        suggest_cases_to_upload(status_db=status_db)
        raise click.Abort

    case_obj = status_db.get_case_by_internal_id(internal_id=family_id)
    chanjo_samples: list[dict] = []
    for link_obj in case_obj.links:
        sample_id = link_obj.sample.internal_id
        chanjo_sample = chanjo_api.sample(sample_id)
        if chanjo_sample is None:
            click.echo(click.style(f"upload coverage for {sample_id}", fg="yellow"))
            continue
        chanjo_samples.append(chanjo_sample)

    if not chanjo_samples:
        return

    coverage_results = chanjo_api.omim_coverage(chanjo_samples)
    for link_obj in case_obj.links:
        sample_id = link_obj.sample.internal_id
        if sample_id in coverage_results:
            completeness = coverage_results[sample_id]["mean_completeness"]
            mean_coverage = coverage_results[sample_id]["mean_coverage"]
            click.echo(f"{sample_id}: {mean_coverage:.2f}X - {completeness:.2f}%")
        else:
            click.echo(click.style(f"{sample_id}: sample not found in chanjo", fg="yellow"))

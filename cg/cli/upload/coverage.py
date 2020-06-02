"""Code for uploading coverage reports via CLI"""

import click

from cg.apps import coverage as coverage_app
from cg.meta.upload.coverage import UploadCoverageApi

from .utils import _suggest_cases_to_upload


@click.command()
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.argument("family_id", required=False)
@click.pass_context
def coverage(context, re_upload, family_id):
    """Upload coverage from an analysis to Chanjo."""

    click.echo(click.style("----------------- COVERAGE --------------------"))

    if not family_id:
        _suggest_cases_to_upload(context)
        context.abort()

    chanjo_api = coverage_app.ChanjoAPI(context.obj)
    family_obj = context.obj["status"].family(family_id)
    api = UploadCoverageApi(context.obj["status"], context.obj["housekeeper_api"], chanjo_api)
    coverage_data = api.data(family_obj.analyses[0])
    api.upload(coverage_data, replace=re_upload)

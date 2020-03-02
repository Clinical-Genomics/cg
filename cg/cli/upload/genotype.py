"""Code for uploading genotype data via CLI"""
import click

from cg.meta.upload.gt import UploadGenotypesAPI

from .utils import _suggest_cases_to_upload


@click.command()
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.argument("family_id", required=False)
@click.pass_context
def genotypes(context, re_upload, family_id):
    """Upload genotypes from an analysis to Genotype."""

    click.echo(click.style("----------------- GENOTYPES -------------------"))

    if not family_id:
        _suggest_cases_to_upload(context)
        context.abort()

    tb_api = context.obj["tb_api"]
    gt_api = context.obj["genotype_api"]
    hk_api = context.obj["housekeeper_api"]
    status_api = context.obj["status"]
    family_obj = status_api.family(family_id)

    api = UploadGenotypesAPI(status_api, hk_api, tb_api, gt_api)
    results = api.data(family_obj.analyses[0])
    if results:
        api.upload(results, replace=re_upload)

"""Code for uploading to scout via CLI"""
import logging

import click

from .utils import _suggest_cases_to_upload

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.option(
    "-p", "--print", "print_console", is_flag=True, help="print config values"
)
@click.argument("case_id", required=False)
@click.pass_context
def scout(context, re_upload, print_console, case_id):
    """Upload variants from analysis to Scout."""

    click.echo(click.style("----------------- SCOUT -----------------------"))

    if not case_id:
        _suggest_cases_to_upload(context)
        context.abort()

    scout_api = context.obj["scout_api"]
    tb_api = context.obj["tb_api"]
    status_api = context.obj["status"]
    scout_upload_api = context.obj["scout_upload_api"]
    hk_api = context.obj["housekeeper_api"]

    family_obj = status_api.family(case_id)
    scout_config = scout_upload_api.generate_config(family_obj.analyses[0])
    if print_console:
        click.echo(scout_config)
        return

    file_path = tb_api.get_family_root_dir(case_id) / "scout_load.yaml"

    if file_path.exists():
        message = (
            "Scout load config %s already exists, you might remove the file and try "
            "again, consider that you might also have it in housekeeper" % file_path
        )
        LOG.warning(message)
        context.abort()

    scout_upload_api.save_config_file(scout_config, file_path)
    try:
        LOG.info("Upload file to housekeeper: %s", file_path)
        scout_upload_api.add_scout_config_to_hk(file_path, hk_api, case_id)
    except FileExistsError as err:
        LOG.warning(
            "%s, consider removing the file from housekeeper and try again", str(err)
        )
        context.abort()

    scout_api.upload(scout_config, force=re_upload)

"""Code for uploading to scout via CLI"""
import logging
from pathlib import Path

import click
import yaml

from cg.apps.hk import HousekeeperAPI
from cg.meta.upload.scoutapi import UploadScoutAPI

from .utils import suggest_cases_to_upload

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.option("-p", "--print", "print_console", is_flag=True, help="print config values")
@click.argument("case_id", required=False)
@click.pass_context
def scout(context, re_upload, print_console, case_id):
    """Upload variants from analysis to Scout."""

    click.echo(click.style("----------------- SCOUT -----------------------"))

    if not case_id:
        suggest_cases_to_upload(context)
        context.abort()

    status_api = context.obj["status_db"]
    scout_upload_api = context.obj["scout_upload_api"]
    hk_api = context.obj["housekeeper_api"]
    family_obj = status_api.family(case_id)
    scout_config = scout_upload_api.generate_config(family_obj.analyses[0])
    mip_dna_root_dir = context.obj["mip-rd-dna"]["root"]

    if print_console:
        click.echo(scout_config)
        return

    file_path = Path(mip_dna_root_dir, case_id, "scout_load.yaml")

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
        LOG.warning("%s, consider removing the file from housekeeper and try again", str(err))
        context.abort()

    context.invoke(upload_case_to_scout, case_id=case_id, re_upload=re_upload)


@click.command()
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.option("--dry-run", is_flag=True)
@click.argument("case_id")
@click.pass_context
def upload_case_to_scout(context, re_upload, dry_run, case_id):
    """Upload variants and case from analysis to Scout."""

    click.echo(click.style("----------------- CONFIG -----------------------"))

    def _get_load_config_from_hk(hk_api: HousekeeperAPI, case_id):
        tag_name = UploadScoutAPI.get_load_config_tag()
        version_obj = hk_api.last_version(case_id)
        scout_config_files = hk_api.get_files(
            bundle=case_id, tags=[tag_name], version=version_obj.id
        )
        if len(list(scout_config_files)) == 0:
            raise FileNotFoundError(f"No scout load config was found in housekeeper for {case_id}")

        return scout_config_files[0].full_path

    scout_api = context.obj["scout_api"]
    hk_api = context.obj["housekeeper_api"]

    load_config = _get_load_config_from_hk(hk_api, case_id)

    LOG.info("uploading case %s to scout", case_id)
    with open(load_config, "r") as stream:
        scout_configs = yaml.safe_load(stream)

    if not dry_run:
        scout_api.upload(scout_configs, force=re_upload)

    click.echo(
        click.style("uploaded to scout using load config {}".format(load_config), fg="green")
    )

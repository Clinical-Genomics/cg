"""Code for uploading to scout via CLI"""
import logging
from pathlib import Path

import click

from cg.apps.hk import HousekeeperAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.store import Store
from cg.store.models import Family
from cg.meta.upload.scoutapi import UploadScoutAPI
from cg.apps.scout.scout_load_config import ScoutLoadConfig

from .utils import suggest_cases_to_upload

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.option("-p", "--print", "print_console", is_flag=True, help="print config values")
@click.argument("case_id", required=False)
@click.pass_context
def scout(context, re_upload: bool, print_console: bool, case_id: str):
    """Upload variants from analysis to Scout."""

    LOG.info("----------------- SCOUT -----------------------")

    if not case_id:
        suggest_cases_to_upload(context)
        context.abort()

    status_api: Store = context.obj["status_db"]
    scout_upload_api: UploadScoutAPI = context.obj["scout_upload_api"]
    family_obj: Family = status_api.family(case_id)
    scout_load_config: ScoutLoadConfig = scout_upload_api.generate_config(family_obj.analyses[0])
    mip_dna_root_dir: Path = Path(context.obj["mip-rd-dna"]["root"])
    if print_console:
        click.echo(scout_load_config.dict(exclude_none=True))
        return

    file_path = mip_dna_root_dir / case_id / "scout_load.yaml"

    if file_path.exists():
        message = (
            "Scout load config %s already exists, you might remove the file and try "
            "again, consider that you might also have it in housekeeper" % file_path
        )
        LOG.warning(message)
        raise click.Abort

    scout_upload_api.save_config_file(scout_load_config, file_path)
    try:
        LOG.info("Upload file to housekeeper: %s", file_path)
        scout_upload_api.add_scout_config_to_hk(config_file_path=file_path, case_id=case_id)
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

    LOG.info("----------------- CONFIG -----------------------")

    def _get_load_config_from_hk(hk_api: HousekeeperAPI, case_id):
        tag_name = UploadScoutAPI.get_load_config_tag()
        version_obj = hk_api.last_version(case_id)
        scout_config_files = hk_api.get_files(
            bundle=case_id, tags=[tag_name], version=version_obj.id
        )
        if len(list(scout_config_files)) == 0:
            raise FileNotFoundError(f"No scout load config was found in housekeeper for {case_id}")

        return scout_config_files[0].full_path

    scout_api: ScoutAPI = context.obj["scout_api"]
    hk_api: HousekeeperAPI = context.obj["housekeeper_api"]

    load_config = _get_load_config_from_hk(hk_api, case_id)

    LOG.info("uploading case %s to scout", case_id)

    if not dry_run:
        scout_api.upload(scout_load_config=load_config, force=re_upload)

    LOG.info("uploaded to scout using load config %s", load_config)

"""Code for uploading to scout via CLI"""
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.meta.upload.scout.scoutapi import UploadScoutAPI
from cg.models.cg_config import CGConfig
from cg.models.scout.scout_load_config import ScoutLoadConfig
from cg.store import Store
from cg.store.models import Family
from housekeeper.store import models as hk_models
from ruamel.yaml import YAML

from .utils import suggest_cases_to_upload

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.option("-p", "--print", "print_console", is_flag=True, help="print config values")
@click.argument("case_id", required=False)
@click.pass_context
def scout(context, re_upload: bool, print_console: bool, case_id: str):
    """Upload variants from analysis to Scout."""
    status_db: Store = context.obj.status_db

    LOG.info("----------------- SCOUT -----------------------")

    if not case_id:
        suggest_cases_to_upload(status_db=status_db)
        return

    context.invoke(
        create_scout_load_config, case_id=case_id, print_console=print_console, re_upload=re_upload
    )
    if not print_console:
        context.invoke(upload_case_to_scout, case_id=case_id, re_upload=re_upload)


@click.command(name="create-scout-load-config")
@click.argument("case-id")
@click.option("-p", "--print", "print_console", is_flag=True, help="Only print config")
@click.option("-r", "--re-upload", is_flag=True, help="Delete existing load configs")
@click.pass_obj
def create_scout_load_config(context: CGConfig, case_id: str, print_console: bool, re_upload: bool):
    """Create a load config for a case in scout and add it to housekeeper"""

    scout_upload_api: UploadScoutAPI = context.meta_apis["scout_upload_api"]
    status_db: Store = context.status_db

    LOG.info("----------------- CREATE CONFIG -----------------------")

    LOG.info("Fetching family object")
    case_obj: Family = status_db.family(case_id)
    LOG.info("Create load config")
    if not case_obj.analyses:
        LOG.warning("Could not find analyses for %s", case_id)
        raise click.Abort
    try:
        scout_load_config: ScoutLoadConfig = scout_upload_api.generate_config(case_obj.analyses[0])
    except SyntaxError as err:
        LOG.warning("%s", err)
        raise click.Abort
    LOG.info("Found load config %s", scout_load_config)
    if scout_load_config.track == "cancer":
        root_dir: Path = Path(context.balsamic.root)
    else:
        root_dir: Path = Path(context.mip_rd_dna.root)
    LOG.info("Set root dir to %s", root_dir)
    file_path: Path = root_dir / case_id / "scout_load.yaml"

    if print_console:
        yaml = YAML()
        yaml.indent(mapping=4, sequence=6, offset=3)
        yaml.dump(scout_load_config.dict(exclude_none=True), sys.stdout)
        LOG.info("Would save file to %s", file_path)
        return

    if file_path.exists():
        LOG.warning("Scout load config %s already exists", file_path)
        if re_upload:
            LOG.info("Deleting old load config")
            file_path.unlink()
        else:
            LOG.info(
                "You might remove the file and try again, consider that you might also have it in housekeeper"
            )
            raise click.Abort
    LOG.info("Saving config file to disc")
    scout_upload_api.save_config_file(upload_config=scout_load_config, file_path=file_path)

    try:
        LOG.info("Add config file to housekeeper")
        scout_upload_api.add_scout_config_to_hk(
            config_file_path=file_path, case_id=case_id, delete=re_upload
        )
    except FileExistsError as err:
        LOG.warning("%s, consider removing the file from housekeeper and try again", str(err))
        raise click.Abort


@click.command(name="upload-case-to-scout")
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.option("--dry-run", is_flag=True)
@click.argument("case_id")
@click.pass_obj
def upload_case_to_scout(context: CGConfig, re_upload: bool, dry_run: bool, case_id: str):
    """Upload variants and case from analysis to Scout."""

    LOG.info("----------------- UPLOAD -----------------------")

    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    scout_api: ScoutAPI = context.scout_api

    tag_name = UploadScoutAPI.get_load_config_tag()
    version_obj = housekeeper_api.last_version(case_id)
    scout_config_file: Optional[hk_models.File] = housekeeper_api.fetch_file_from_version(
        version_obj=version_obj, tags={tag_name}
    )

    if scout_config_file is None:
        raise FileNotFoundError(f"No scout load config was found in housekeeper for {case_id}")

    LOG.info("uploading case %s to scout", case_id)

    if not dry_run:
        scout_api.upload(scout_load_config=scout_config_file.full_path, force=re_upload)

    LOG.info("uploaded to scout using load config %s", scout_config_file.full_path)
    LOG.info("Case loaded successfully to Scout")

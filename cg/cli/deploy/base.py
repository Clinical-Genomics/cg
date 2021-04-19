"""CLI for deploying tools with CG"""

import logging
from pathlib import Path

import click
from cg.apps.shipping import ShippingAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group()
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def deploy(context: CGConfig, dry_run: bool):
    """Deploy tools with CG. Use --help to see what tools are available"""
    LOG.info("Running CG DEPLOY")
    shipping_api = context.shipping_api
    shipping_api.set_dry_run(dry_run)


@click.command(name="fluffy")
@click.pass_obj
def deploy_fluffy_cmd(context: CGConfig):
    """Deploy the fluffy tool"""
    LOG.info("Deploying fluffy with CG")
    fluffy_config: Path = Path(context.fluffy.deploy_config)
    shipping_api: ShippingAPI = context.shipping_api
    shipping_api.deploy(app_name="fluffy", app_config=fluffy_config)


@click.command(name="genotype")
@click.pass_obj
def deploy_genotype_cmd(context: CGConfig):
    """Deploy the genotype tool"""
    LOG.info("Deploying genotype with CG")
    shipping_api: ShippingAPI = context.shipping_api
    shipping_api.deploy(app_name="genotype")


@click.command(name="hermes")
@click.pass_obj
def deploy_hermes_cmd(context: CGConfig):
    """Deploy the hermes tool"""
    LOG.info("Deploying hermes with CG")
    hermes_config: Path = Path(context.hermes.deploy_config)
    shipping_api: ShippingAPI = context.shipping_api
    shipping_api.deploy(app_name="hermes", app_config=hermes_config)


@click.command(name="loqusdb")
@click.pass_obj
def deploy_loqusdb_cmd(context: CGConfig):
    """Deploy the LoqusDB tool"""
    LOG.info("Deploying LoqusDB with CG")
    shipping_api: ShippingAPI = context.shipping_api
    shipping_api.deploy(app_name="loqusdb")


@click.command(name="scout")
@click.pass_obj
def deploy_scout_cmd(context: CGConfig):
    """Deploy the scout tool"""
    LOG.info("Deploying scout-browser with CG")
    scout_config: Path = Path(context.scout.deploy_config)
    shipping_api: ShippingAPI = context.shipping_api
    shipping_api.deploy(app_name="scout", app_config=scout_config)


@click.command(name="shipping")
@click.pass_obj
def deploy_shipping_cmd(context: CGConfig):
    """Deploy the shipping tool"""
    LOG.info("Deploying shipping with CG")
    shipping_api: ShippingAPI = context.shipping_api
    shipping_api.deploy(app_name="shipping")


deploy.add_command(deploy_fluffy_cmd)
deploy.add_command(deploy_genotype_cmd)
deploy.add_command(deploy_hermes_cmd)
deploy.add_command(deploy_loqusdb_cmd)
deploy.add_command(deploy_scout_cmd)
deploy.add_command(deploy_shipping_cmd)

"""CLI for deploying tools with CG"""

import logging
from pathlib import Path

import click

from cg.apps.shipping import ShippingAPI

LOG = logging.getLogger(__name__)


@click.group()
@click.option("--dry-run", is_flag=True)
@click.pass_context
def deploy(context, dry_run):
    """Deploy tools with CG. Use --help to see what tools are available"""
    LOG.info("Running CG DEPLOY")
    shipping_api = ShippingAPI(context.obj["shipping"])
    shipping_api.set_dry_run(dry_run)
    context.obj["shipping_api"] = shipping_api


@click.command(name="shipping")
@click.pass_context
def deploy_shipping_cmd(context):
    """Deploy the shipping tool"""
    LOG.info("Deploying shipping with CG")
    shipping_api: ShippingAPI = context.obj["shipping_api"]
    shipping_api.deploy(app_name="shipping")


@click.command(name="hermes")
@click.pass_context
def deploy_hermes_cmd(context):
    """Deploy the hermes tool"""
    LOG.info("Deploying hermes with CG")
    hermes_config: Path = Path(context.obj["hermes"]["deploy_config"])
    shipping_api: ShippingAPI = context.obj["shipping_api"]
    shipping_api.deploy(app_name="hermes", app_config=hermes_config)


@click.command(name="fluffy")
@click.pass_context
def deploy_fluffy_cmd(context):
    """Deploy the fluffy tool"""
    LOG.info("Deploying fluffy with CG")
    fluffy_config: Path = Path(context.obj["fluffy"]["deploy_config"])
    shipping_api: ShippingAPI = context.obj["shipping_api"]
    shipping_api.deploy(app_name="fluffy", app_config=fluffy_config)


@click.command(name="genotype")
@click.pass_context
def deploy_genotype_cmd(context):
    """Deploy the genotype tool"""
    LOG.info("Deploying genotype with CG")
    shipping_api: ShippingAPI = context.obj["shipping_api"]
    shipping_api.deploy(app_name="genotype")


@click.command(name="scout")
@click.pass_context
def deploy_scout_cmd(context):
    """Deploy the scout tool"""
    LOG.info("Deploying scout-browser with CG")
    scout_config: Path = Path(context.obj["scout"]["deploy_config"])
    shipping_api: ShippingAPI = context.obj["shipping_api"]
    shipping_api.deploy(app_name="scout", app_config=scout_config)


deploy.add_command(deploy_shipping_cmd)
deploy.add_command(deploy_genotype_cmd)
deploy.add_command(deploy_scout_cmd)
deploy.add_command(deploy_fluffy_cmd)
deploy.add_command(deploy_hermes_cmd)

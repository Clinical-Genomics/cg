"""CLI for deploying tools with CG"""

import logging

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


@click.command(name="genotype")
@click.pass_context
def deploy_genotype_cmd(context):
    """Deploy the shipping tool"""
    LOG.info("Deploying genotype with CG")
    shipping_api: ShippingAPI = context.obj["shipping_api"]
    shipping_api.deploy(app_name="genotype")


deploy.add_command(deploy_shipping_cmd)
deploy.add_command(deploy_genotype_cmd)

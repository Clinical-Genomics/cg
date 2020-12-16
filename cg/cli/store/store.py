"""Code for store part of CLI"""

import logging

import click

from .analysis import store_analysis_cmd
from .fastq import fastq

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def store(context):
    """Command for storing files"""
    LOG.info("Running CG store command")


store.add_command(fastq)
store.add_command(store_analysis_cmd)

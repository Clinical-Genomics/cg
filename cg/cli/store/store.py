"""Code for store part of CLI"""

import logging

import click

from .fastq import fastq

LOG = logging.getLogger(__name__)


@click.group()
def store():
    """Command for storing files"""
    LOG.info("Running CG store command")


store.add_command(fastq)

"""Code for uploading all completed analyses via SLI"""
import logging
import sys
import traceback

import click

from .upload import upload

LOG = logging.getLogger(__name__)

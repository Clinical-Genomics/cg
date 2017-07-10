# -*- coding: utf-8 -*-
from trailblazer.mip.start import MipCli
from trailblazer.store import Store
from trailblazer.cli.utils import environ_email
from trailblazer.mip import files

from .add import AddHandler


class TrailblazerAPI(Store, AddHandler):
    """docstring for TrailblazerAPI"""

    def __init__(self, config):
        super(TrailblazerAPI, self).__init__(config['trailblazer']['database'])
        self.mip_cli = MipCli(config['trailblazer']['script'])
        self.mip_config = config['trailblazer']['mip_config']

    def start(self, family_id: str, priority: str='normal', email: str=None):
        """Start MIP."""
        email = email or environ_email()
        kwargs = dict(config=self.mip_config, family=family_id, priority=priority, email=email)
        self.mip_cli(**kwargs)
        self.add_pending(family_id, email=email)

    @staticmethod
    def parse_qcmetrics(data: dict) -> dict:
        """Call internal Trailblazer MIP API."""
        return files.parse_qcmetrics(data)

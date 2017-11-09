# -*- coding: utf-8 -*-
import logging
import shutil
from pathlib import Path
from typing import List

import click
from trailblazer.mip.start import MipCli
from trailblazer.store import Store
from trailblazer.cli.utils import environ_email
from trailblazer.mip import files, fastq

from .add import AddHandler

log = logging.getLogger(__name__)


class TrailblazerAPI(Store, AddHandler, fastq.FastqHandler):

    """Interface to Trailblazer for `cg`."""

    parse_sampleinfo = staticmethod(files.parse_sampleinfo)

    def __init__(self, config: dict):
        super(TrailblazerAPI, self).__init__(
            config['trailblazer']['database'],
            families_dir=config['trailblazer']['root'],
        )
        self.mip_cli = MipCli(config['trailblazer']['script'])
        self.mip_config = config['trailblazer']['mip_config']

    def start(self, family_id: str, priority: str='normal', email: str=None,
              skip_evaluation: bool=False):
        """Start MIP."""
        email = email or environ_email()
        kwargs = dict(config=self.mip_config, family=family_id, priority=priority, email=email)
        if skip_evaluation:
            kwargs['skip_evaluation'] = True
        self.mip_cli(**kwargs)
        self.add_pending(family_id, email=email)

    @staticmethod
    def parse_qcmetrics(data: dict) -> dict:
        """Call internal Trailblazer MIP API."""
        return files.parse_qcmetrics(data)

    def write_panel(self, family_id: str, content: List[str]):
        """Write the gene panel to the defined location."""
        out_dir = Path(self.families_dir) / family_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / 'aggregated_master.bed'
        with out_path.open('w') as out_handle:
            for line in content:
                click.echo(line, file=out_handle)

    def delete_analysis(self, family, date, yes=False):
        """Delete the analysis output."""

        analysis_obj = self.find_analysis(family, date, 'completed')
        analysis_path = Path(analysis_obj.out_dir).parent

        if yes or click.confirm(f"Do you want to remove {analysis_path}?"):
            shutil.rmtree(analysis_path, ignore_errors=True)

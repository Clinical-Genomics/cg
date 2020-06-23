import gzip
import logging
import re
import subprocess
import sys
import shutil
import click

from cg.apps import hk, lims
from cg.apps.balsamic.fastq import FastqHandler
from cg.utils.fastq import FastqAPI
from cg.cli.workflow.balsamic.store import store as store_cmd
from cg.cli.workflow.balsamic.deliver import deliver as deliver_cmd
from cg.cli.workflow.get_links import get_links
from cg.exc import LimsDataError, BalsamicStartError
from cg.meta.workflow.base import get_target_bed_from_lims
from cg.meta.workflow.balsamic import AnalysisAPI
from cg.store import Store
from cg.utils.commands import Process
from pathlib import Path
from cg.utils.fastq import FastqAPI


LOG = logging.getLogger(__name__)


class BalsamicAPI:
    """Handles execution of BALSAMIC"""

    def __init__(self, config):
        self.binary = config["balsamic"]["executable"]
        self.singularity = config["balsamic"]["singularity"]
        self.reference_config = config["balsamic"]["reference_config"]
        self.email = config["balsamic"]["email"]
        self.root_dir = config["balsamic"]["root"]
        self.slurm = config["balsamic"]["slurm"]["account"]
        self.qos = config["balsamic"]["slurm"]["qos"]
        self.process = Process(self.binary)

    def config_case(self, arguments: dict):
        """Create config file for BALSAMIC analysis"""

        command = ("config", "case")

        opts = {
            "--analysis-dir": self.root_dir,
            "--singularity": self.singularity,
            "--reference-config": self.reference_config,
            "--case-id": arguments["case_id"],
            "--normal": arguments["normal"],
            "--output-config": arguments["output_config"],
            "--panel-bed": arguments["panel_bed"],
            "--tumor": arguments["tumor"],
        }

        opts = sum([(k, v) for k, v in opts if v], ())
        self.process.run_command(command + opts)

    def run_analysis(self, arguments: dict):
        """Execute BALSAMIC"""

        command = ("run", "analysis")

        opts = {
            "--account": self.slurm,
            "--mail-user": self.email,
            "--qos": self.qos,
            "--sample-config": Path(self.root_dir) / arguments["case_id"] / arguments["case_id"]
            + ".json",
            "--analysis-type": arguments["analysis_type"],
            "--run-analysis": arguments["run_analysis"],
        }

        opts = sum([(k, v) for k, v in opts if v], ())
        self.process.run_command(command)

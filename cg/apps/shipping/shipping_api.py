"""API to the deployment tool Shipping"""

import logging
from pathlib import Path
from typing import Dict

from cg.utils import Process

LOG = logging.getLogger(__name__)


class ShippingAPI:
    """Class to communicate with the tool shipping

    Shipping is used as a unified tool for deploying in the Clinical Genomics environments
    """

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.host_config = config["host_config"]
        self.binary_path = config["binary_path"]
        self.process = Process(
            binary=str(self.binary_path), config=self.host_config, config_parameter="--host-config"
        )
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Update dry run"""
        LOG.info("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    def deploy(self, app_name: str, app_config: Path = None):
        """Command to deploy a tool according to the specifications in the config files"""
        LOG.info("Deploying the %s software", app_name)
        deploy_args = []
        if app_config:
            LOG.info("Use app config %s", app_config)
            deploy_args.extend(["--app-config", str(app_config)])
        else:
            deploy_args.extend(["--tool-name", app_name])

        deploy_args.append("deploy")
        self.process.run_command(deploy_args, dry_run=self.dry_run)
        for line in self.process.stderr_lines():
            LOG.info(line)

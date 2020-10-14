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

    def deploy(self, app_config: Path = None, app_name: str = None):
        """Command to deploy a tool according to the specifications in the config files"""
        deploy_args = []
        if app_config:
            deploy_args.extend(["--app-config", str(app_config)])
        elif app_name:
            deploy_args.extend(["--tool-name", app_name])
        else:
            LOG.warning("Please specify what application to deploy")
            raise SyntaxError
        deploy_args.append("deploy")
        self.process.run_command(deploy_args, dry_run=self.dry_run)
        for line in self.process.stderr_lines():
            LOG.info(line)

    def deploy_shipping(self):
        """Deploy the tool shipping

        Deployment of shipping does not need any extra information since it is following the regular workflow
        with conda environments using standard names
        """
        LOG.info("Deploying the shipping software")
        self.deploy(app_name="shipping")

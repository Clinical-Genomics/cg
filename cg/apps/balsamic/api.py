import logging
from typing import Dict, List

from cg.utils.commands import Process

LOG = logging.getLogger(__name__)


class BalsamicAPI:
    """Handles execution of BALSAMIC"""

    __EXIT_SUCCESS = 0

    def __init__(self, config: dict):
        self.binary = config["balsamic"]["binary_path"]
        self.singularity = config["balsamic"]["singularity"]
        self.reference_config = config["balsamic"]["reference_config"]
        self.root_dir = config["balsamic"]["root"]
        self.account = config["balsamic"]["slurm"]["account"]
        self.email = config["balsamic"]["slurm"]["mail_user"]
        self.qos = config["balsamic"]["slurm"]["qos"]
        self.bed_path = config["bed_path"]
        self.process = Process(self.binary)

    def __build_command_str(self, options: dict) -> List[str]:
        formatted_options = []
        for key, val in options.items():
            if val:
                formatted_options.append(str(key))
                formatted_options.append(str(val))
        return formatted_options

    def config_case(self, arguments: dict, dry: bool = False) -> int:
        """Create config file for BALSAMIC analysis """

        command = ["config", "case"]
        options = self.__build_command_str(
            {
                "--analysis-dir": self.root_dir,
                "--singularity": self.singularity,
                "--reference-config": self.reference_config,
                "--case-id": arguments.get("case_id"),
                "--normal": arguments.get("normal"),
                "--tumor": arguments.get("tumor"),
                "--panel-bed": arguments.get("panel_bed"),
                "--umi-trim-length": arguments.get("umi_trim_length"),
            }
        )
        parameters = command + options
        if dry:
            LOG.info(f'Dry run command balsamic {" ".join(parameters)}')
            retcode = self.__EXIT_SUCCESS
        else:
            retcode = self.process.run_command(parameters=parameters)
        return retcode

    def run_analysis(self, arguments: dict, run_analysis: bool, dry: bool = False) -> int:
        """Execute BALSAMIC run analysis with given options"""

        command = ["run", "analysis"]
        run_analysis = ["--run-analysis"] if run_analysis else []
        options = self.__build_command_str(
            {
                "--account": self.account,
                "--mail-user": arguments.get("email", self.email),
                "--qos": arguments.get("priority", self.qos),
                "--sample-config": arguments.get("sample_config"),
                "--analysis-type": arguments.get("analysis_type"),
                "--disable-variant-caller": arguments.get("disable_variant_caller"),
            }
        )
        parameters = command + options + run_analysis
        if dry:
            LOG.info(f'Dry run command balsamic {" ".join(parameters)}')
            retcode = self.__EXIT_SUCCESS
        else:
            retcode = self.process.run_command(parameters=parameters)
        return retcode

    def report_deliver(self, arguments: dict, dry: bool = False) -> int:
        """Execute BALSAMIC report deliver with given options"""

        command = ["report", "deliver"]
        options = self.__build_command_str(
            {
                "--sample-config": arguments.get("sample_config"),
                "--analysis-type": arguments.get("analysis_type"),
            }
        )
        parameters = command + options
        if dry:
            LOG.info(f'Dry run command balsamic {" ".join(parameters)}')
            retcode = self.__EXIT_SUCCESS
        else:
            retcode = self.process.run_command(parameters=parameters)
        return retcode

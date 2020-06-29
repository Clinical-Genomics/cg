import logging
from cg.utils.commands import Process
from pathlib import Path

LOG = logging.getLogger(__name__)


class BalsamicAPI:
    """Handles execution of BALSAMIC"""

    EXIT_SUCCESS = 0

    def __init__(self, config):
        self.binary = config["balsamic"]["binary_path"]
        self.singularity = config["balsamic"]["singularity"]
        self.reference_config = config["balsamic"]["reference_config"]
        self.root_dir = config["balsamic"]["root"]
        self.account = config["balsamic"]["slurm"]["account"]
        self.email = config["balsamic"]["slurm"]["mail_user"]
        self.qos = config["balsamic"]["slurm"]["qos"]
        self.bed_path = config["bed_path"]
        self.process = Process(self.binary)

    def __build_command_str(self, options) -> list:
        formatted_options = []
        for key, val in options.items():
            if val:
                formatted_options.append(str(key))
                formatted_options.append(str(val))
        return formatted_options

    def config_case(self, arguments: dict, dry: bool):
        """Create config file for BALSAMIC analysis"""

        command = ["config", "case"]
        options = {
            "--analysis-dir": self.root_dir,
            "--singularity": self.singularity,
            "--reference-config": self.reference_config,
            "--case-id": arguments.get("case_id"),
            "--normal": arguments.get("normal"),
            "--tumor": arguments.get("tumor"),
            "--output-config": arguments.get("output_config"),
            "--panel-bed": arguments.get("panel_bed"),
            "--adapter-trim": arguments.get("adapter_trim"),
            "--quality-trim": arguments.get("quality_trim"),
            "--umi": arguments.get("umi"),
            "--umi-trim-length": arguments.get("umi_trim_length"),
        }

        options = self.__build_command_str(options)

        if dry:
            LOG.info(f'Executing command balsamic{" ".join(command + options)}')
            retcode = self.EXIT_SUCCESS
        else:
            retcode = self.process.run_command(command + options)
        return retcode

    def run_analysis(self, arguments: dict, run_analysis: bool, dry: bool):
        """Execute BALSAMIC"""

        command = ["run", "analysis"]
        run_analysis = ["--run-analysis"] if run_analysis else []
        options = {
            "--account": self.account,
            "--mail-user": arguments.get("email") or self.email,
            "--qos": arguments.get("priority") or self.qos,
            "--sample-config": arguments.get("sample_config"),
            "--analysis-type": arguments.get("analysis_type"),
        }
        options = self.__build_command_str(options)
        if dry:
            LOG.info(f'Executing command balsamic{" ".join(command + options + run_analysis)}')
            retcode = self.EXIT_SUCCESS
        else:
            retcode = self.process.run_command(command + options + run_analysis)
        return retcode

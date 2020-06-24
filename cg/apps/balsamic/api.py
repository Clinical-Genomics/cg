import logging
from cg.utils.commands import Process
from pathlib import Path

LOG = logging.getLogger(__name__)


class BalsamicAPI:
    """Handles execution of BALSAMIC"""
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

    def config_case(self, arguments: dict, dry: bool):
        """Create config file for BALSAMIC analysis"""

        command = ("config", "case")
        opts = {
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

        opts = sum([(k, str(v)) for k, v in opts.items() if v], ())

        if dry:
            LOG.info(f'Executing command {" ".join(command + opts)}')
            return 0
        else:
            retcode = self.process.run_command(command + opts)
            return retcode

    def run_analysis(self, arguments: dict, dry: bool):
        """Execute BALSAMIC"""
        command = ("run", "analysis")

        opts = {
            "--account": self.account,
            "--mail-user": self.email,
            "--qos": self.qos,
            "--sample-config": arguments.get("sample_config"),
            "--analysis-type": arguments.get("analysis_type"),
            "--run-analysis": arguments.get("run_analysis"),
        }

        opts = sum([(k, str(v)) for k, v in opts.items() if v], ())

        if dry:
            LOG.info(f'Executing command {" ".join(command + opts)}')
            return 0
        else:
            retcode = self.process.run_command(command + opts)
            return retcode

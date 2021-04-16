"""
    Module for mutacc-auto API
"""

import copy
import json
import logging
import subprocess

LOG = logging.getLogger(__name__)


class MutaccAutoAPI:

    """
    API for mutacc-auto
    """

    def __init__(self, config: dict):

        self.mutacc_auto_config = config["mutacc_auto"]["config_path"]
        self.mutacc_auto_binary = config["mutacc_auto"]["binary_path"]
        self.mutacc_padding = config["mutacc_auto"]["padding"]
        self.base_call = [self.mutacc_auto_binary, "--config-file", self.mutacc_auto_config]

    def extract_reads(self, case: dict, variants: dict):
        """
        Use mutacc-auto extract command to extract the relevant reads from
        the case

        Args:
            case (dict): case dictionary from scout
            variants (dict): variants dict from scout
            padding (int): padding (bp:s) around genomic region of variant

        """

        extract_call = copy.deepcopy(self.base_call)

        def json_default_decoder(obj):
            """ decode to str if object is not serializable"""
            return str(obj)

        extract_call.extend(
            [
                "extract",
                "--variants",
                json.dumps(variants, default=json_default_decoder),
                "--case",
                json.dumps(case, default=json_default_decoder),
                "--padding",
                str(self.mutacc_padding),
            ]
        )

        run_command(extract_call)

    def import_reads(self):

        """
        Upload the cases and extracted reads to mutacc DB
        """

        import_call = copy.deepcopy(self.base_call)
        import_call.extend(["import"])

        run_command(import_call)


def run_command(command: list):

    """
    Use subprocess.run to run command

    Args:
        command (list): list of commands
    """

    completed_process = subprocess.run(args=command, check=False)
    returncode = completed_process.returncode
    if returncode != 0:
        LOG.warning("process %s ended with exitcode %d", " ".join(command), returncode)
        raise subprocess.CalledProcessError(returncode=returncode, cmd=command)

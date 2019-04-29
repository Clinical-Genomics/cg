# -*- coding: utf-8 -*-

"""
    Module for loqusdb API
"""

import json
import copy
import logging

import subprocess
from subprocess import CalledProcessError

from cg.exc import CaseNotFoundError

LOG = logging.getLogger(__name__)


class LoqusdbAPI():

    """
        API for loqusdb
    """

    def __init__(self, config: dict):
        super(LoqusdbAPI, self).__init__()

        self.password = config['loqusdb']['password']
        self.username = config['loqusdb']['username']
        self.port = config['loqusdb']['port']
        self.host = config['loqusdb'].get('host') or 'localhost'
        self.db_name = config['loqusdb']['database_name']
        self.loqusdb_binary = config['loqusdb']['binary']

        # This will allways be the base of the loqusdb call
        self.base_call = [self.loqusdb_binary, '-db', self.db_name,
                          '--username', self.username,
                          '--password', self.password,
                          '--host', self.host,
                          '--port', str(self.port)]

    def load(self, family_id: str, ped_path: str, vcf_path: str, vcf_sv_path: str,
             gbcf_path: str) -> dict:
        """Add observations from a VCF."""
        load_call = copy.deepcopy(self.base_call)
        load_call.extend([
            'load',
            '-c', family_id,
            '-f', ped_path,
            '--variant-file', vcf_path,
            '--sv-variants', vcf_sv_path,
            '--check-profile', gbcf_path,
            '--hard-threshold', '0.95',
            '--soft-threshold', '0.90'
            ])

        nr_variants = 0
        # Execute command and print its stdout+stderr as it executes
        for line in execute_command(load_call):
            log_msg = f"loqusdb output: {line}"
            LOG.info(log_msg)
            line_content = line.split('INFO')[-1].strip()
            if 'inserted' in line_content:
                nr_variants = int(line_content.split(':')[-1].strip())

        return dict(variants=nr_variants)

    def get_case(self, case_id: str) -> dict:
        """Find a case in the database by case id."""
        case_obj = None
        case_call = copy.deepcopy(self.base_call)

        case_call.extend(['cases', '-c', case_id, '--to-json'])

        try:
            output = subprocess.check_output(
                ' '.join(case_call),
                shell=True
            )

        except CalledProcessError:
            # If CalledProcessError is raised, log and raise error
            log_msg = f"Could not run command: {' '.join(case_call)}"
            LOG.critical(log_msg)
            raise

        output = output.decode('utf-8')

        # If case not in loqusdb, stdout of loqusdb command will be empty.
        if not output:
            raise CaseNotFoundError(f"Case {case_id} not found in loqusdb")

        case_obj = json.loads(output)[0]

        return case_obj

    def __repr__(self):
        uri = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        return (f"LoqusdbAPI(uri={uri},"
                f"db_name={self.db_name},"
                f"loqusdb_binary={self.loqusdb_binary})")


def execute_command(cmd):
    """
        Prints stdout + stderr of command in real-time while being executed

        Args:
            cmd (list): command sequence

        Yields:
            line (str): line of output from command
    """
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               bufsize=1)

    for line in process.stdout:
        yield line.decode('utf-8').strip()

    # Check if process exited with returncode != 0
    if process.poll():
        raise CalledProcessError(returncode=process.returncode, cmd=cmd)

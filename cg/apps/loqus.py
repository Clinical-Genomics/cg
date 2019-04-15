# -*- coding: utf-8 -*-
import json
import copy
import logging

import subprocess
from subprocess import CalledProcessError

LOG = logging.getLogger(__name__)

class LoqusdbAPI(object):

    def __init__(self, config: dict):
        super(LoqusdbAPI, self).__init__()
        self.uri = config['loqusdb']['database']

        #For loqusdb v1.0 (Does not take an uri)
        self.password = config['loqusdb']['password']
        self.username = config['loqusdb']['username']
        self.port = config['loqusdb']['port']
        self.host = config['loqusdb'].get('host') or 'localhost'

        self.db_name = config['loqusdb']['database_name']
        self.loqusdb_binary = config['loqusdb']['binary']
        ## This will allways be the base of the loqusdb call
        self.base_call = [self.loqusdb_binary, '-db', self.db_name,
                          '--username', self.username,
                          '--password', self.password,
                          '--host', self.host,
                          '--port', str(self.port)]

    def load(self, family_id: str, ped_path: str, vcf_path: str) -> dict:
        """Add observations from a VCF."""
        load_call = copy.deepcopy(self.base_call)
        load_call.extend([
            'load', '-c', family_id, '-f', ped_path, vcf_path,
        ])

        output = subprocess.check_output(
            ' '.join(load_call),
            shell=True,
            stderr=subprocess.STDOUT,
        )

        nr_variants = 0
        # Parse log output to get number of inserted variants
        for line in output.decode('utf-8').split('\n'):
            log_message = (line.split('INFO'))[-1].strip()
            if 'inserted' in log_message:
                nr_variants = int(log_message.split(':')[-1].strip())

        return dict(variants=nr_variants)

    def get_case(self, case_id: str) -> dict:
        """Find a case in the database by case id."""
        case_obj = None
        case_call = copy.deepcopy(self.base_call)

        #For loqusdb v1
        #loqusdb cases -c is unstable in loqusdb. Here all variants are found
        #through loqusdb cases (skipping the --case-id option), and the cases
        #are parsed for the correct case_id
        case_call.extend(['cases'])

        #For loqusdb v2
        #case_call.extend(['cases', '-c', case_id, '--to-json'])

        try:
            output = subprocess.check_output(
                        ' '.join(case_call),
                        shell=True
                    )

        except CalledProcessError as err:
            # If case does not exist we will get a non zero exit code and return None
            return case_obj

        if output.decode('utf-8') == '':
            # If case does not exist, empty string will be returned. If so, return None
            return case_obj

        #For loqusdb v1
        #parse through the output lines to see if case is in loqusdb
        for line in output.decode('utf-8').split('\n'):

            if line == '':
                continue

            json_line = line.replace("ObjectId(", '').replace(")", '').replace("'",'"')
            case = json.loads(json_line)
            if case_id == case['case_id']:
                case_obj = case
                break

        # The output is a list of dictionaries that are case objs
        #case_obj = json.loads(output.decode('utf-8'))[0]

        if case_obj:
            LOG.debug(f"case {case_obj['case_id']} with '_id' {case_obj['_id']} found")
        else:
            LOG.debug(f"case {case_id} not in loqusdb")

        return case_obj

    def __repr__(self):
        return f"LoqusdbAPI(uri={self.uri},db_name={self.db_name},loqusdb_binary={self.loqusdb_binary})"

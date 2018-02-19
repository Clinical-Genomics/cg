import json

import pytest

from cg.meta.report.api import ReportAPI
import datetime


class MockLims():

    def get_samples(self, udf):
        return lims_exported_samples()

    def get_prep_method(self, lims_id: str) -> str:
        return 'CG002 - End repair Size selection A-tailing and Adapter ligation (TruSeq PCR-free ' \
               '' \
               'DNA)'

    def get_sequencing_method(self, lims_id: str) -> str:
        return 'CG002 - Cluster Generation (HiSeq X)'

    def get_delivery_method(self, lims_id: str) -> str:
        return 'CG002 - Delivery'

    def get_processing_time(self, lims_id: str) -> str:
        return datetime.datetime.today() - datetime.datetime.today()

    def get_delivery_date(self, lims_id: str) -> str:
        return datetime.datetime.today()

    def family(self, customer: str, family: str):
        """Fetch information about a family of samples."""
        filters = {'customer': customer, 'familyID': family}
        samples_data = self.get_samples(udf=filters)

        # get family level data
        family_data = {'family': family, 'customer': customer, 'samples': []}
        priorities = set()
        panels = set()
        for sample_data in samples_data:
            priorities.add(sample_data['priority'])
            if sample_data['panels']:
                panels.update(sample_data['panels'])
            family_data['samples'].append(sample_data)

        if len(priorities) == 1:
            family_data['priority'] = priorities.pop()
        elif 'express' in priorities:
            family_data['priority'] = 'express'
        elif 'priority' in priorities:
            family_data['priority'] = 'priority'
        elif 'standard' in priorities:
            family_data['priority'] = 'standard'

        family_data['panels'] = list(panels)
        return family_data


class MockTB():

    def get_trending(self, mip_config_raw: dict, qcmetrics_raw: dict, sampleinfo_raw: dict) -> dict:
        # Returns: dict: parsed data
        ### Define output dict
        outdata = {
            'analysis_sex': {'female'},
            'family': 'yellowhog',
            'duplicates': {'13.525'},
            'genome_build': 'hg19',
            'mapped_reads': {'98.8'},
            'mip_version': 'v4.0.20',
            'sample_ids': ['2018-20203', '2018-20204'],
        }

        return outdata

class MockDeliver():

    def get_post_analysis_files(self, family: str, version, tag):

        if tag == 'mip-config':
            return ['/mnt/hds/proj/bioinfo/bundles/' + family + '/2018-01-30/' + family + \
                '_config.yaml']
        elif tag == 'sampleinfo':
            return ['/mnt/hds/proj/bioinfo/bundles/' + family + '/2018-01-30/' + family + \
                '_qc_sample_info.yaml']
        if tag == 'qcmetrics':
            return ['/mnt/hds/proj/bioinfo/bundles/' + family + '/2018-01-30/' + family + \
                '_qc_metrics.yaml']


@pytest.fixture(scope='function')
def report_api(base_store):
    lims = MockLims()
    tb = MockTB()
    deliver = MockDeliver()
    _report_api = ReportAPI(lims_api=lims, db=base_store, tb_api=tb, deliver_api=deliver)
    return _report_api


@pytest.fixture
def case_data_path():
    _in_data_path = 'tests/fixtures/cli/report/case_data.json'
    return _in_data_path


@pytest.fixture
def case_data(case_data_path):
    return json.load(open(case_data_path))


@pytest.fixture
def lims_exported_samples():
    return json.load(open('tests/fixtures/cli/report/lims_exported_samples.json'))

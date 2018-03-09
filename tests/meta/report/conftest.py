import json

import pytest

from cg.meta.report.api import ReportAPI
import datetime

from cg.store import Store


class MockLims:

    def get_prep_method(self, lims_id: str) -> str:
        return 'CG002 - End repair Size selection A-tailing and Adapter ligation (TruSeq PCR-free ' \
               '' \
               '' \
               '' \
               '' \
               '' \
               '' \
               '' \
               '' \
               '' \
               '' \
               '' \
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

    def sample(self, lims_id: str):
        """Fetch information about a sample."""
        samples = lims_family().get('samples')

        for sample in samples:
            if sample.get('id') == lims_id:
                return sample

        return None


class MockTB:
    _get_trending_raises_keyerror = False

    def get_trending(self, mip_config_raw: dict, qcmetrics_raw: dict, sampleinfo_raw: dict) -> dict:
        if self._get_trending_raises_keyerror:
            raise KeyError

        # Returns: dict: parsed data
        ### Define output dict
        outdata = {
            'analysis_sex': {'ADM1': 'female', 'ADM2': 'female', 'ADM3': 'female'},
            'family': 'yellowhog',
            'duplicates': {'ADM1': 13.525, 'ADM2': 12.525, 'ADM3': 14.525},
            'genome_build': 'hg19',
            'mapped_reads': {'ADM1': 98.8, 'ADM2': 99.8, 'ADM3': 97.8},
            'mip_version': 'v4.0.20',
            'sample_ids': ['2018-20203', '2018-20204'],
        }

        return outdata


class MockFile:

    def __init__(self, path):
        self.path = path


class MockDeliver:
    _get_post_analysis_files_returns_none = False

    def get_post_analysis_files(self, family: str, version, tags: [str]):

        if self._get_post_analysis_files_returns_none:
            return None

        if tags[0] == 'mip-config':
            path = '/mnt/hds/proj/bioinfo/bundles/' + family + '/2018-01-30/' + family + \
                   '_config.yaml'
        elif tags[0] == 'sampleinfo':
            path = '/mnt/hds/proj/bioinfo/bundles/' + family + '/2018-01-30/' + family + \
                   '_qc_sample_info.yaml'
        elif tags[0] == 'qcmetrics':
            path = '/mnt/hds/proj/bioinfo/bundles/' + family + '/2018-01-30/' + family + \
                   '_qc_metrics.yaml'

        return [MockFile(path=path)]

    def get_post_analysis_files_root_dir(self):
        return ''


class MockChanjo:
    _sample_coverage_returns_none = False

    def sample_coverage(self, sample_id) -> dict:
        """Calculate coverage for OMIM panel."""

        if self._sample_coverage_returns_none:
            return None

        if sample_id == 'ADM1':
            data = {'mean_coverage': 38.342,
                    'mean_completeness': 99.1,
                    }
        elif sample_id == 'ADM2':
            data = {
                'mean_coverage': 37.342,
                'mean_completeness': 97.1,
            }
        else:
            data = {
                'mean_coverage': 39.342,
                'mean_completeness': 98.1,
            }

        return data

    def sample(self, sample_id: str) -> dict:
        """Fetch sample from the database."""
        return {'id': sample_id}


class MockPath:
    _path = None

    def __call__(self, path):
        self._path = path
        return self

    def joinpath(self, another_path):
        return self(self._path + another_path)

    def open(self):
        pass


class MockAnalysis:
    def panel(self, family_obj) -> [str]:
        """Create the aggregated panel file."""
        return ['']


class MockLogger:
    last_warning = None
    warnings = []

    def warning(self, text: str):
        self.last_warning = text
        self.warnings.append(text)

    def get_last_warning(self) -> str:
        return self.last_warning

    def get_warnings(self) -> list:
        return self.warnings


class MockYamlLoader:
    def __init__(self):
        self.open_file = None

    def safe_load(self, open_file: str):
        self.open_file = open_file
        return 'safely_loaded_file'

    def get_open_file(self):
        return self.open_file


@pytest.fixture
def lims_family():
    return json.load(open('tests/fixtures/report/lims_family.json'))


@pytest.fixture
def lims_samples():
    return lims_family()['samples']


class MockDB(Store):
    _family_samples_returns_no_reads = False
    _application_accreditation = None

    def __init__(self, store):
        self.store = store

    def family_samples(self, family_id: str):

        family_samples = self.store.family_samples(family_id)

        if self._family_samples_returns_no_reads:
            for family_sample in family_samples:
                family_sample.sample.reads = None

        return family_samples

    def application(self, tag: str):
        """Fetch an application from the store."""
        application = self.store.application(tag=tag)

        if self._application_accreditation is not None:
            application.is_accredited = self._application_accreditation

        return application


class MockReport(ReportAPI):
    _fileToOpen = ''

    def __init__(self, db, lims_api, tb_api, deliver_api, chanjo_api, analysis_api, logger,
                 yaml_loader,
                 path_tool):
        self.db = db
        self.lims = lims_api
        self.tb = tb_api
        self.deliver = deliver_api
        self.chanjo = chanjo_api
        self.analysis = analysis_api
        self.LOG = logger
        self.yaml_loader = yaml_loader
        self.path_tool = path_tool


@pytest.fixture(scope='function')
def report_api(analysis_store):
    db = MockDB(analysis_store)
    lims = MockLims()
    tb = MockTB()
    deliver = MockDeliver()
    chanjo = MockChanjo()
    analysis = MockAnalysis()
    logger = MockLogger()
    yaml_loader = MockYamlLoader()
    path_tool = MockPath()
    _report_api = MockReport(lims_api=lims, db=db, tb_api=tb, deliver_api=deliver,
                             chanjo_api=chanjo, analysis_api=analysis, logger=logger,
                             yaml_loader=yaml_loader,
                             path_tool=path_tool)
    return _report_api

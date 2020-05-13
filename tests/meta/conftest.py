import pytest
from _pytest import tmpdir

from cg.apps.balsamic.fastq import FastqHandler as BalsamicFastqHandler
from cg.apps.crunchy import CrunchyAPI
from cg.apps.hk import HousekeeperAPI
from cg.apps.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.usalt.fastq import FastqHandler as MicrosaltFastqHandler
from cg.meta.compress import CompressAPI
from cg.meta.deliver import DeliverAPI
from cg.meta.workflow.mip_dna import AnalysisAPI


@pytest.yield_fixture(scope="function")
def scout_store():
    """Setup Scout adapter."""
    yield None


@pytest.yield_fixture(scope="function")
def trailblazer_api(tmpdir):
    """Setup Trailblazer api."""
    root_path = tmpdir.mkdir("families")
    _store = TrailblazerAPI(
        {
            "trailblazer": {
                "database": "sqlite://",
                "root": str(root_path),
                "script": ".",
                "mip_config": ".",
            }
        }
    )
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.yield_fixture(scope="function")
def housekeeper_api(tmpdir):
    """Setup Housekeeper store."""
    root_path = tmpdir.mkdir("bundles")
    _api = HousekeeperAPI(
        {"housekeeper": {"database": "sqlite://", "root": str(root_path)}}
    )
    _api.initialise_db()
    yield _api
    _api.destroy_db()


@pytest.fixture
def analysis_family():
    """Build an example family."""
    family = {
        "name": "family",
        "internal_id": "yellowhog",
        "panels": ["IEM", "EP"],
        "samples": [
            {
                "name": "son",
                "sex": "male",
                "internal_id": "ADM1",
                "father": "ADM2",
                "mother": "ADM3",
                "status": "affected",
                "ticket_number": 123456,
                "reads": 5000000,
                "capture_kit": "GMSmyeloid",
                "data_analysis": "PIM",
            },
            {
                "name": "father",
                "sex": "male",
                "internal_id": "ADM2",
                "status": "unaffected",
                "ticket_number": 123456,
                "reads": 6000000,
                "capture_kit": "GMSmyeloid",
                "data_analysis": "PIM",
            },
            {
                "name": "mother",
                "sex": "female",
                "internal_id": "ADM3",
                "status": "unaffected",
                "ticket_number": 123456,
                "reads": 7000000,
                "capture_kit": "GMSmyeloid",
                "data_analysis": "PIM",
            },
        ],
    }
    return family


@pytest.yield_fixture(scope="function")
def analysis_store(base_store, analysis_family):
    """Setup a store instance for testing analysis API."""
    customer = base_store.customer("cust000")
    family = base_store.Family(
        name=analysis_family["name"],
        panels=analysis_family["panels"],
        internal_id=analysis_family["internal_id"],
        priority="standard",
    )
    family.customer = customer
    base_store.add(family)
    application_version = base_store.application("WGTPCFC030").versions[0]
    for sample_data in analysis_family["samples"]:
        sample = base_store.add_sample(
            name=sample_data["name"],
            sex=sample_data["sex"],
            internal_id=sample_data["internal_id"],
            ticket=sample_data["ticket_number"],
            reads=sample_data["reads"],
            capture_kit=sample_data["capture_kit"],
            data_analysis=sample_data["data_analysis"],
        )
        sample.family = family
        sample.application_version = application_version
        sample.customer = customer
        base_store.add(sample)
    base_store.commit()
    for sample_data in analysis_family["samples"]:
        sample_obj = base_store.sample(sample_data["internal_id"])
        link = base_store.relate_sample(
            family=family,
            sample=sample_obj,
            status=sample_data["status"],
            father=base_store.sample(sample_data["father"])
            if sample_data.get("father")
            else None,
            mother=base_store.sample(sample_data["mother"])
            if sample_data.get("mother")
            else None,
        )
        base_store.add(link)
    base_store.commit()
    yield base_store


class MockCrunchy(CrunchyAPI):

    pass


class MockVersion:
    """Mock a version object"""

    @property
    def id(self):
        return ""


class MockFile:
    """Mock a file object"""

    def __init__(self, path="", to_archive=False, tags=None):
        self.path = path
        self.to_archive = to_archive
        self._tags = []
        if tags:
            for tag in tags:
                self._tags.append(MockTag(tag))

    def full_path(self):
        return ""

    def is_included(self):
        return False

    @property
    def tags(self):
        return self._tags


class MockFiles:
    """Mock file objects"""

    def __init__(self, files):
        self._files = files

    def all(self):
        return self._files

    def first(self):
        return self._files[0]


class MockTag:
    """Mock a file object"""

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name


class MockHouseKeeper(HousekeeperAPI):
    """Mock the housekeeper API"""

    # In this mock we want to override __init__ so disable here
    def __init__(self, files: MockFiles = None):
        self._file_added = False
        self._file_included = False
        self._files = MockFiles([])
        if files:
            self._files = files
        self._file = MockFile()

    # This is overriding a housekeeper object so ok to not include all arguments
    def files(self, bundle, version, tags):
        """Mock the files method to return a list of files"""
        files = []

        for file in self._files.all():
            if any(tag.name in tags for tag in file.tags):
                files.append(file)

        return MockFiles(files)

    def get_files(self, bundle, tags, version="1.0"):
        """Mock the get_files method to return a list of files"""
        return self._files

    def add_file(self, file, version_obj, tag_name, to_archive=False):
        """Mock the add_files method to add a MockFile to the list of files"""
        self._file_added = True
        self._file = MockFile(path=file)
        return self._file

    def version(self, bundle: str, date: str):
        """Fetch version from the database."""
        return MockVersion()

    def last_version(self, bundle: str):
        """docstring for last_version"""
        return MockVersion()

    def include_file(self, file_obj, version_obj):
        """docstring for include_file"""
        self._file_included = True

    def add_commit(self, file_obj):
        """Overrides sqlalchemy method"""
        return file_obj

    def get_root_dir(self):
        """Overrides sqlalchemy method"""
        return self._file


class MockScoutAPI(ScoutAPI):
    """Mock class for Scout api"""

    def __init__(self):
        pass


class MockLims:
    """Mock lims fixture"""

    lims = None

    def __init__(self):
        self.lims = self


class MockDeliver(DeliverAPI):
    def __init__(self):
        self.housekeeper = MockHouseKeeper()
        self.lims = MockLims()

    def get_post_analysis_files(self, case: str, version, tags):

        if tags[0] == "mip-config":
            path = (
                "/mnt/hds/proj/bioinfo/bundles/"
                + case
                + "/2018-01-30/"
                + case
                + "_config.yaml"
            )
        elif tags[0] == "sampleinfo":
            path = (
                "/mnt/hds/proj/bioinfo/bundles/"
                + case
                + "/2018-01-30/"
                + case
                + "_qc_sample_info.yaml"
            )
        if tags[0] == "qcmetrics":
            path = (
                "/mnt/hds/proj/bioinfo/bundles/"
                + case
                + "/2018-01-30/"
                + case
                + "_qc_metrics.yaml"
            )

        return [MockFile(path=path)]

    def get_post_analysis_case_files(self, case: str, version, tags):
        return ""

    def get_post_analysis_files_root_dir(self):
        return ""


class MockPath:
    def __init__(self, path):
        self.yaml = None

    def __call__(self, *args, **kwargs):
        return self

    def open(self):
        return dict()

    def joinpath(self, path):
        return ""


class MockLogger:
    warnings = []

    def warning(self, text, *interpolations):

        self.warnings.append(text % interpolations)

    def get_warnings(self) -> list:
        return self.warnings


class MockTB:
    _get_trending_raises_keyerror = False

    def __init__(self):
        """Needed to initialise mock variables"""
        self._make_config_was_called = False

    def get_trending(
        self, mip_config_raw: dict, qcmetrics_raw: dict, sampleinfo_raw: dict
    ) -> dict:
        if self._get_trending_raises_keyerror:
            raise KeyError("mockmessage")

        # Returns: dict: parsed data
        ### Define output dict
        outdata = {
            "analysis_sex": {"ADM1": "female", "ADM2": "female", "ADM3": "female"},
            "family": "yellowhog",
            "duplicates": {"ADM1": 13.525, "ADM2": 12.525, "ADM3": 14.525},
            "genome_build": "hg19",
            "mapped_reads": {"ADM1": 98.8, "ADM2": 99.8, "ADM3": 97.8},
            "mip_version": "v4.0.20",
            "sample_ids": ["2018-20203", "2018-20204"],
            "genome_build": "37",
            "rank_model_version": "1.18",
        }

        return outdata

    def get_sampleinfo(self, analysis_obj):
        return ""

    def make_config(self, data, pipeline):
        """Mock the make_config"""
        self._make_config_was_called = True
        del pipeline
        return data


class MockBalsamicFastq(BalsamicFastqHandler):
    """Mock FastqHandler for analysis_api"""

    def __init__(self):
        super().__init__(config={"balsamic": {"root": tmpdir}})


class MockMicrosaltFastq(MicrosaltFastqHandler):
    """Mock FastqHandler for analysis_api"""

    def __init__(self):
        super().__init__(config={"usalt": {"root": tmpdir}})


def safe_loader(path):
    """Mock function for loading yaml"""

    if path:
        pass

    return {
        "human_genome_build": {"version": ""},
        "recipe": {"rankvariant": {"rank_model": {"version": 1.18}}},
    }


@pytest.yield_fixture(scope="function")
def analysis_api(analysis_store, housekeeper_api, scout_store):
    """Setup an analysis API."""
    Path_mock = MockPath("")
    tb_mock = MockTB()

    _analysis_api = AnalysisAPI(
        db=analysis_store,
        hk_api=housekeeper_api,
        scout_api=scout_store,
        tb_api=tb_mock,
        lims_api=None,
        deliver_api=MockDeliver(),
        yaml_loader=safe_loader,
        path_api=Path_mock,
        logger=MockLogger(),
    )
    yield _analysis_api


@pytest.yield_fixture(scope="function")
def deliver_api(analysis_store):
    """Fixture for deliver_api"""
    lims_mock = MockLims()
    hk_mock = MockHouseKeeper()
    hk_mock.add_file(file="/mock/path", version_obj="", tag_name="")
    hk_mock._files = MockFiles(
        [MockFile(tags=["case-tag"]), MockFile(tags=["sample-tag", "ADM1"])]
    )

    _api = DeliverAPI(
        db=analysis_store,
        hk_api=hk_mock,
        lims_api=lims_mock,
        case_tags=["case-tag"],
        sample_tags=["sample-tag"],
    )

    yield _api

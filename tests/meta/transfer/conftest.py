import datetime as dt

import pytest
from cg.apps.cgstats.db import models as stats_models
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.meta.transfer import TransferLims
from cg.meta.transfer.flowcell import TransferFlowcell
from cg.store import Store, models


@pytest.fixture(name="data")
def fixture_data() -> dict:
    return {
        "samples": [
            {
                "name": "ADM1136A3",
                "index": "ACGTACAT",
                "flowcell": "HJKMYBCXX",
                "type": "hiseqx",
            }
        ]
    }


@pytest.fixture(scope="function")
def store_stats() -> StatsAPI:
    """Setup base CGStats store."""
    _store = StatsAPI({"cgstats": {"database": "sqlite://", "root": "tests/fixtures/DEMUX"}})
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.fixture(scope="function")
def base_store_stats(store_stats: StatsAPI, data: dict) -> StatsAPI:
    """Setup CGStats store with sample data."""
    demuxes = {}
    for sample_data in data["samples"]:
        project: stats_models.Project = store_stats.Project(
            projectname="test", time=dt.datetime.now()
        )
        sample: stats_models.Sample = store_stats.Sample(
            samplename=sample_data["name"],
            barcode=sample_data["index"],
            limsid=sample_data["name"],
        )
        sample.project = project
        unaligned: stats_models.Unaligned = store_stats.Unaligned(
            readcounts=300000000, q30_bases_pct=85
        )
        unaligned.sample = sample

        if sample_data["flowcell"] in demuxes:
            demux = demuxes[sample_data["flowcell"]]
        else:
            flowcell: stats_models.Flowcell = store_stats.Flowcell(
                flowcellname=sample_data["flowcell"],
                flowcell_pos="A",
                hiseqtype=sample_data["type"],
                time=dt.datetime.now(),
            )
            supportparams: stats_models.Supportparams = store_stats.Supportparams(
                document_path="NA", idstring="NA"
            )
            datasource: stats_models.Datasource = store_stats.Datasource(
                document_path="NA", document_type="html"
            )
            datasource.supportparams = supportparams
            demux = store_stats.Demux()
            demux.flowcell = flowcell
            demux.datasource = datasource
            demuxes[sample_data["flowcell"]] = demux

        unaligned.demux = demux
        store_stats.add(unaligned)
    store_stats.commit()
    yield store_stats


@pytest.fixture(scope="function")
def flowcell_store(base_store: Store, data: dict) -> Store:
    """Setup store with sample data for testing flowcell transfer."""
    for sample_data in data["samples"]:
        customer_obj: models.Customer = base_store.customers().first()
        application_version: models.ApplicationVersion = base_store.application(
            "WGTPCFC030"
        ).versions[0]
        sample: models.Sample = base_store.add_sample(
            name="NA", sex="male", internal_id=sample_data["name"]
        )
        sample.customer = customer_obj
        sample.application_version = application_version
        sample.received_at = dt.datetime.now()
        base_store.add(sample)
    base_store.commit()
    yield base_store


@pytest.fixture(scope="function")
def transfer_flowcell_api(
    flowcell_store: Store, housekeeper_api: HousekeeperAPI, base_store_stats: StatsAPI
) -> TransferFlowcell:
    """Setup flowcell transfer API."""
    transfer_api = TransferFlowcell(
        db=flowcell_store, stats_api=base_store_stats, hk_api=housekeeper_api
    )
    yield transfer_api


@pytest.fixture(scope="function")
def transfer_lims_api(sample_store: Store) -> TransferLims:
    """Setup flowcell transfer API."""
    yield TransferLims(sample_store, MockLims(config=""))


class MockLims(LimsAPI):
    def __init__(self, config):
        pass

    _received_at = None
    _delivered_at = None
    _prepared_date = None
    _samples = []

    def get_received_date(self, lims_id: str):

        received_date = None
        for sample in self._samples:
            if sample.internal_id == lims_id:
                received_date = sample.received_at
        return received_date

    def mock_set_samples(self, samples):
        self._samples = samples


@pytest.fixture(scope="function")
def lims_api():

    _lims_api = MockLims(config="")
    return _lims_api

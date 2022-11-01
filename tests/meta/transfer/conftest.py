import datetime as dt
from typing import List

import pytest
from cg.apps.cgstats.db import models as stats_models
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.transfer import TransferLims
from cg.meta.transfer.flowcell import TransferFlowcell
from cg.store import Store, models
from pathlib import Path

from tests.mocks.limsmock import MockLimsAPI


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
    _store = StatsAPI(
        {
            "cgstats": {
                "binary_path": "echo",
                "database": "sqlite://",
                "root": "tests/fixtures/DEMUX",
            }
        }
    )
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
    """Setup store with sample data for testing flow cell transfer."""
    for sample_data in data["samples"]:
        customer_obj: models.Customer = base_store.customers().first()
        application_version: models.ApplicationVersion = base_store.application(
            "WGSPCFC030"
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
    """Setup flow cell transfer API."""
    yield TransferFlowcell(db=flowcell_store, stats_api=base_store_stats, hk_api=housekeeper_api)


@pytest.fixture(name="transfer_lims_api")
def fixture_transfer_lims_api(sample_store: Store) -> TransferLims:
    """Setup LIMS transfer API."""
    yield TransferLims(sample_store, MockLimsAPI(config=""))


@pytest.fixture(name="external_data_directory", scope="session")
def external_data_directory(
    tmpdir_factory, customer_id: str, cust_sample_id: str, ticket: str
) -> Path:
    """Returns a customer folder with fastq.gz files in sample-directories."""
    cust_folder: Path = tmpdir_factory.mktemp(customer_id, numbered=False)
    ticket_folder: Path = Path(cust_folder, ticket)
    ticket_folder.mkdir()
    samples: List[str] = [f"{cust_sample_id}1", f"{cust_sample_id}2"]
    for sample in samples:
        Path(ticket_folder, sample).mkdir(exist_ok=True, parents=True)
        for read in [1, 2]:
            Path(ticket_folder, sample, f"{sample}_fastq_{read}.fastq.gz").touch(exist_ok=True)
            Path(ticket_folder, sample, f"{sample}_fastq_{read}.fastq.gz.md5").touch(exist_ok=True)
    return Path(ticket_folder)

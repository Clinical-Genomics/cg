import datetime as dt

import pytest

from cg.apps.stats import StatsAPI
from cg.meta.transfer.flowcell import TransferFlowcell


@pytest.fixture
def data():
    return {
        'samples': [{
            'name': 'ADM1136A3',
            'index': 'ACGTACAT',
            'flowcell': 'HJKMYBCXX',
            'type': 'hiseqx',
        }]
    }


@pytest.yield_fixture(scope='function')
def store_stats():
    """Setup base CGStats store."""
    _store = StatsAPI({'cgstats': {'database': 'sqlite://', 'root': 'tests/fixtures/DEMUX'}})
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.yield_fixture(scope='function')
def base_store_stats(store_stats, data):
    """Setup CGStats store with sample data."""
    demuxes = {}
    for sample_data in data['samples']:
        project = store_stats.Project(projectname='test', time=dt.datetime.now())
        sample = store_stats.Sample(samplename=sample_data['name'], barcode=sample_data['index'],
                                    limsid=sample_data['name'])
        sample.project = project
        unaligned = store_stats.Unaligned(readcounts=300000000, q30_bases_pct=85)
        unaligned.sample = sample

        if sample_data['flowcell'] in demuxes:
            demux = demuxes[sample_data['flowcell']]
        else:
            flowcell = store_stats.Flowcell(flowcellname=sample_data['flowcell'], flowcell_pos='A',
                                            hiseqtype=sample_data['type'], time=dt.datetime.now())
            supportparams = store_stats.Supportparams(document_path='NA', idstring='NA')
            datasource = store_stats.Datasource(document_path='NA', document_type='html')
            datasource.supportparams = supportparams
            demux = store_stats.Demux()
            demux.flowcell = flowcell
            demux.datasource = datasource
            demuxes[sample_data['flowcell']] = demux

        unaligned.demux = demux
        store_stats.add(unaligned)
    store_stats.commit()
    yield store_stats


@pytest.yield_fixture(scope='function')
def flowcell_store(base_store, data):
    """Setup store with sample data for testing flowcell transfer."""
    for sample_data in data['samples']:
        customer_obj = base_store.customers().first()
        application_version = base_store.application('WGTPCFC030').versions[0]
        sample = base_store.add_sample(name='NA', sex='male', internal_id=sample_data['name'])
        sample.customer = customer_obj
        sample.application_version = application_version
        sample.received_at = dt.datetime.now()
        base_store.add(sample)
    base_store.commit()
    yield base_store


@pytest.yield_fixture(scope='function')
def transfer_flowcell_api(flowcell_store, store_housekeeper, base_store_stats):
    """Setup flowcell transfer API."""
    transfer_api = TransferFlowcell(flowcell_store, base_store_stats, store_housekeeper)
    yield transfer_api

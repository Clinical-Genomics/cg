import datetime as dt

from cg.apps.lims import LimsAPI
from cg.meta.transfer import TransferLims
from cg.meta.transfer.lims import IncludeOptions, SampleState
from cg.store import Store


def has_same_received_at(lims, sample_obj):
    lims_received_date = lims.get_received_date(lims_id=sample_obj.internal_id)
    return sample_obj.received_at == lims_received_date


def test_transfer_samples_received_at_overwriteable(
    transfer_lims_api: TransferLims, timestamp_now: dt.datetime
):
    # GIVEN a sample that exists in statusdb and it has a received_at date but no delivered_at date,
    # there is a sample in lims with the same internal id and another received_at date
    lims_api: LimsAPI = transfer_lims_api.lims
    sample_store: Store = transfer_lims_api.status
    assert sample_store.samples_to_deliver().count() > 0
    sample = sample_store.samples_to_deliver().first()
    assert sample.received_at
    lims_samples = [
        sample_store.add_sample(
            name=sample.name, sex=sample.sex, internal_id=sample.internal_id, received=timestamp_now
        )
    ]

    lims_api.set_samples(lims_samples)
    assert not has_same_received_at(lims_api, sample)

    # WHEN transfer_samples has been called
    transfer_lims_api.transfer_samples(SampleState.RECEIVED, IncludeOptions.NOTINVOICED.value)

    # THEN the samples should have the same received_at as in lims
    assert has_same_received_at(lims_api, sample)


def test_transfer_samples_all(transfer_lims_api: TransferLims, timestamp_now: dt.datetime):
    # GIVEN a sample exists in statusdb and it has a received_at date but no delivered_at date,
    # there is a sample in lims with the same internal id and another received_at date
    lims_api = transfer_lims_api.lims
    sample_store = transfer_lims_api.status
    assert sample_store.samples_to_deliver().count() > 0
    sample = sample_store.samples_to_deliver().first()
    assert sample.received_at
    lims_samples = [
        sample_store.add_sample(
            name=sample.name, sex=sample.sex, internal_id=sample.internal_id, received=timestamp_now
        )
    ]
    lims_api.set_samples(lims_samples)
    assert not has_same_received_at(lims_api, sample)

    # WHEN transfer_samples has been called
    transfer_lims_api.transfer_samples(SampleState.RECEIVED, IncludeOptions.ALL.value)

    # THEN the samples should have the same received_at as in lims
    assert has_same_received_at(lims_api, sample)


def test_transfer_samples_include_unset_received_at(transfer_lims_api: TransferLims):
    sample_store = transfer_lims_api.status
    samples = sample_store.samples()
    assert samples.count() >= 2

    # GIVEN sample with unset received_at
    untransfered_sample = samples[0]
    untransfered_sample.received_at = None
    untransfered_sample.preped_at = None
    untransfered_sample.sequenced_at = None
    untransfered_sample.delivered_at = None

    # GIVEN sample with set received_at
    transfered_sample = samples[1]
    transfered_sample.received_at = dt.datetime.today()
    transfered_sample.preped_at = None
    transfered_sample.sequenced_at = None
    transfered_sample.delivered_at = None

    # GIVEN both samples has received date in lims
    untransfered_sample_received_at_date = dt.datetime.today()
    transfered_sample_received_at_date = dt.datetime.today()
    lims_sample = sample_store.add_sample(
        name=untransfered_sample.name,
        sex=untransfered_sample.sex,
        internal_id=untransfered_sample.internal_id,
        received=untransfered_sample_received_at_date,
    )
    lims_samples = [lims_sample]
    lims_sample = sample_store.add_sample(
        name=transfered_sample.name,
        sex=transfered_sample.sex,
        internal_id=transfered_sample.internal_id,
        received=transfered_sample_received_at_date,
    )
    lims_samples.append(lims_sample)
    lims_api = transfer_lims_api.lims
    lims_api.set_samples(lims_samples)

    # WHEN calling transfer lims with include unset received_at
    transfer_lims_api.transfer_samples(SampleState.RECEIVED, IncludeOptions.UNSET.value)

    # THEN the sample that was not set has been set and the other sample was not touched
    assert has_same_received_at(lims_api, untransfered_sample)
    assert not has_same_received_at(lims_api, transfered_sample)

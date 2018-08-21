import datetime as dt
from cg.meta.transfer.lims import SampleState


def has_same_received_at(lims, sample_obj):
    status_date = lims.get_received_date(lims_id=sample_obj.internal_id)
    print("sample_obj.received_at: ", sample_obj.received_at)
    print("LIMS status_date", status_date)

    return sample_obj.received_at == status_date


def test_transfer_samples_received_at_overwriteable(transfer_lims_api):

    # GIVEN a sample exists in statusdb and it has a received_at date but no delivered_at date,
    # there is a sample in lims with the same internal id and another received_at date
    lims_api = transfer_lims_api.lims
    sample_store = transfer_lims_api.status
    assert sample_store.samples_to_deliver().count() > 0
    sample = sample_store.samples_to_deliver().first()
    assert sample.received_at
    new_date = dt.datetime.today()
    lims_sample = sample_store.add_sample(name=sample.name, sex=sample.sex,
                                          internal_id=sample.internal_id,
                                          received=new_date)
    lims_api.mock_set_samples(lims_sample)
    assert not has_same_received_at(lims_api, sample)

    # WHEN transfer_samples has been called
    transfer_lims_api.transfer_samples(SampleState.RECEIVED)

    # THEN the samples should have the same received_at as in lims
    assert has_same_received_at(lims_api, sample)

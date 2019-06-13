from cg.store import Store
from cg.store.api.sync import sync_applications


def test_sync_microbial_orderform_dryrun(microbial_store: Store, microbial_orderform):

    # GIVEN a microbial orderform and a store where all the apptags exists half some inactive and
    # some active

    prep_category = 'mic'
    sign='PG'
    activate=False
    inactivate=False
    active_mic_applications_from_start = base_store.applications(category=prep_category,
                                                                 archived=False)
    inactive_mic_applications_from_start = base_store.applications(category=prep_category,
                                                                   archived=True)

    # WHEN syncing app-tags in that orderform
    sync_applications(store = base_store, excel_path=microbial_orderform,
                      prep_category=prep_category, sign=sign, activate=activate,
                      inactivate=inactivate, sheet_name='Drop down list', tag_column=2)

    # THEN same number of active mic applications in status database
    active_mic_applications_after_when = base_store.applications(category=prep_category,
                                                                 archived=False)
    inactive_mic_applications_after_when = base_store.applications(category=prep_category,
                                                                   archived=True)
    assert active_mic_applications_from_start == active_mic_applications_after_when
    assert inactive_mic_applications_from_start == inactive_mic_applications_after_when

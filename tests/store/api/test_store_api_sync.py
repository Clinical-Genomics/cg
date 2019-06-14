"""Test store api sync methods"""

from cg.store import Store
from cg.store.api.sync import sync_apptags


def test_sync_microbial_orderform_dryrun(base_store: Store, microbial_orderform):
    # GIVEN a microbial orderform and a store where all the apptags exists half some inactive and
    # some active
    ensure_applications(base_store, ['MWRNXTR003', 'MWGNXTR003', 'MWMNXTR003', 'MWLNXTR003'],
                        ['MWXNXTR003', 'VWGNXTR001', 'VWLNXTR001'])
    prep_category = 'mic'
    sign = 'PG'
    activate = False
    inactivate = False
    active_mic_apps_from_start = base_store.applications(category=prep_category,
                                                         archived=False).count()
    inactive_mic_apps_from_start = base_store.applications(category=prep_category,
                                                           archived=True).count()

    # WHEN syncing app-tags in that orderform
    sync_apptags(store=base_store, excel_path=microbial_orderform,
                 prep_category=prep_category, sign=sign, activate=activate,
                 inactivate=inactivate, sheet_name='Drop down list', tag_column=2)

    # THEN same number of active and inactive mic applications in status database
    active_mic_apps_after_when = base_store.applications(category=prep_category,
                                                         archived=False).count()
    inactive_mic_apps_after_when = base_store.applications(category=prep_category,
                                                           archived=True).count()
    assert active_mic_apps_from_start == active_mic_apps_after_when
    assert inactive_mic_apps_from_start == inactive_mic_apps_after_when


def test_sync_microbial_orderform_activate(base_store: Store, microbial_orderform):
    # GIVEN a microbial orderform and a store where all the apptags exists half some inactive and
    # some active
    ensure_applications(base_store, ['MWRNXTR003', 'MWGNXTR003', 'MWMNXTR003', 'MWLNXTR003'],
                        ['MWXNXTR003', 'VWGNXTR001', 'VWLNXTR001'])
    prep_category = 'mic'
    sign = 'PG'
    activate = True
    inactivate = False
    active_mic_apps_from_start = base_store.applications(category=prep_category,
                                                         archived=False).count()
    inactive_mic_apps_from_start = base_store.applications(category=prep_category,
                                                           archived=True).count()

    # WHEN syncing app-tags in that orderform
    sync_apptags(store=base_store, excel_path=microbial_orderform,
                 prep_category=prep_category, sign=sign, activate=activate,
                 inactivate=inactivate, sheet_name='Drop down list', tag_column=2)

    # THEN more active mic applications in status database and same inactive
    active_mic_apps_after_when = base_store.applications(category=prep_category,
                                                         archived=False).count()
    inactive_mic_apps_after_when = base_store.applications(category=prep_category,
                                                           archived=True).count()
    assert active_mic_apps_from_start < active_mic_apps_after_when
    assert inactive_mic_apps_from_start > inactive_mic_apps_after_when


def test_sync_microbial_orderform_inactivate(base_store: Store, microbial_orderform):
    # GIVEN a microbial orderform and a store where all the apptags exists half some inactive and
    # some active
    ensure_applications(base_store, ['MWRNXTR003', 'MWGNXTR003', 'MWMNXTR003', 'MWLNXTR003',
                                     'dummy_tag'],
                        ['MWXNXTR003', 'VWGNXTR001', 'VWLNXTR001'])
    prep_category = 'mic'
    sign = 'PG'
    activate = False
    inactivate = True
    active_mic_apps_from_start = base_store.applications(category=prep_category,
                                                         archived=False).count()
    inactive_mic_apps_from_start = base_store.applications(category=prep_category,
                                                           archived=True).count()

    # WHEN syncing app-tags in that orderform
    sync_apptags(store=base_store, excel_path=microbial_orderform,
                 prep_category=prep_category, sign=sign, activate=activate,
                 inactivate=inactivate, sheet_name='Drop down list', tag_column=2)

    # THEN same number of active and more inactive mic applications in status database
    active_mic_apps_after_when = base_store.applications(category=prep_category,
                                                         archived=False).count()
    inactive_mic_apps_after_when = base_store.applications(category=prep_category,
                                                           archived=True).count()
    assert active_mic_apps_from_start > active_mic_apps_after_when
    assert inactive_mic_apps_from_start < inactive_mic_apps_after_when


def ensure_applications(base_store: Store, active_applications: list, inactive_applications: list):
    """Create some requested applications for the tests """
    for active_application in active_applications:
        if not base_store.application(active_application):
            base_store.add_commit(base_store.add_application(active_application, 'mic',
                                                             'dummy_description',
                                                             is_archived=False))

    for inactive_application in inactive_applications:
        if not base_store.application(inactive_application):
            base_store.add_commit(base_store.add_application(inactive_application, 'mic',
                                                             'dummy_description', is_archived=True))

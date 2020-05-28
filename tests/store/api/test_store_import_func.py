"""Tests for reset part of the store API"""

from cg.store import Store
from cg.store.api.import_func import (
    prices_are_same,
    versions_are_same,
    import_application_versions,
    _get_tag_from_raw_version,
    add_version_from_raw,
    import_applications,
    _get_tag_from_raw_application,
    import_apptags,
    XlFileHelper,
    XlSheetHelper,
)


def test_prices_are_same_int_and_int():
    # GIVEN float price that looks like one in excel
    # GIVEN same price but as it looks when saved in database
    float_price = 0.0
    database_price = 0

    # WHEN calling prices are same
    should_be_same = prices_are_same(database_price, float_price)

    # THEN prices should be considered same
    assert should_be_same


def test_prices_are_not_same_int_and_int():
    # GIVEN float price that looks like one in excel
    # GIVEN same price but as it looks when saved in database
    float_price = 1.0
    database_price = 0

    # WHEN calling prices are same
    should_not_be_same = prices_are_same(database_price, float_price)

    # THEN prices should be considered same
    assert not should_not_be_same


def test_prices_are_same_float_and_int():
    # GIVEN float price that looks like one in excel
    # GIVEN same price but as it looks when saved in database
    float_price = 0.654345
    database_price = 1

    # WHEN calling prices are same
    should_be_same = prices_are_same(database_price, float_price)

    # THEN prices should be considered same
    assert should_be_same


def test_prices_are_same_float_and_float():
    # GIVEN float price that looks like one in excel
    # GIVEN same price but as it looks when saved in database
    float_price = 0.654345
    database_price = float_price

    # WHEN calling prices are same
    should_be_same = prices_are_same(database_price, float_price)

    # THEN prices should be considered same
    assert should_be_same


def test_versions_are_same(store: Store, application_versions_file):
    # GIVEN an excel price row
    # same price row committed to the database
    add_applications(store, application_versions_file)
    raw_version = XlFileHelper.get_raw_dicts_from_xl(application_versions_file)[0]
    tag = _get_tag_from_raw_version(raw_version)
    application_obj = store.application(tag)
    sign = "DummySign"
    workbook = XlFileHelper.get_workbook_from_xl(application_versions_file)
    db_version = add_version_from_raw(application_obj, None, raw_version, sign, store, workbook)
    datemode = XlFileHelper.get_datemode_from_xl(application_versions_file)

    # WHEN calling versions are same
    should_be_same = versions_are_same(db_version, raw_version, datemode)

    # THEN versions are considered same
    assert should_be_same


def test_versions_are_not_same(store, application_versions_file):
    # GIVEN an excel price row
    # NOT same price row committed to the database
    add_applications(store, application_versions_file)
    raw_version = XlFileHelper.get_raw_dicts_from_xl(application_versions_file)[0]
    tag = _get_tag_from_raw_version(raw_version)
    application_obj = store.application(tag)
    sign = "DummySign"
    workbook = XlFileHelper.get_workbook_from_xl(application_versions_file)
    db_version = add_version_from_raw(application_obj, None, raw_version, sign, store, workbook)
    datemode = XlFileHelper.get_datemode_from_xl(application_versions_file)
    another_raw_version = XlFileHelper.get_raw_dicts_from_xl(application_versions_file)[1]

    # WHEN calling versions are same
    should_not_be_same = versions_are_same(db_version, another_raw_version, datemode)

    # THEN versions are not considered same
    assert not should_not_be_same


def test_application_version(application_versions_file, store: Store):
    # GIVEN a store with applications
    # and an excel file with prices for those applications
    add_applications(store, application_versions_file)
    sign = "TestSign"

    # WHEN calling import_application_version
    import_application_versions(
        store, application_versions_file, sign, dry_run=False, skip_missing=False
    )

    # THEN versions should have been created in the store
    assert all_versions_exists_in_store(store, application_versions_file)


def test_application_version_dry_run(application_versions_file, store: Store):
    # GIVEN a store with applications
    # and an excel file with prices for those applications
    add_applications(store, application_versions_file)
    sign = "TestSign"

    # WHEN calling import_application_version as dry run
    import_application_versions(
        store, application_versions_file, sign, dry_run=True, skip_missing=False
    )

    # THEN versions should not have been created in the store
    assert not all_versions_exists_in_store(store, application_versions_file)


def test_application(applications_file, store: Store):
    # GIVEN a store and an excel file with applications
    sign = "TestSign"

    # WHEN calling import_applications
    import_applications(store, applications_file, sign, dry_run=False)

    # THEN applications should have been created in the store
    assert all_applications_exists(store, applications_file)


def test_application_sheet_name(applications_file, store: Store):
    # GIVEN a store and an excel file with applications
    sign = "TestSign"

    # WHEN calling import_applications
    import_applications(store, applications_file, sign, dry_run=False, sheet_name="application")

    # THEN applications should have been created in the store
    assert all_applications_exists(store, applications_file)


def test_application_dry_run(applications_file, store: Store):
    # GIVEN a store and an excel file with applications
    sign = "TestSign"

    # WHEN calling import_applications as dry run
    import_applications(store, applications_file, sign, dry_run=True)

    # THEN applications should not have been created in the store
    assert not all_applications_exists(store, applications_file)


def test_sync_microbial_orderform_dryrun(base_store: Store, microbial_orderform):
    # GIVEN a microbial orderform and a store where all the apptags exists half some inactive and
    # some active
    ensure_applications(
        base_store,
        ["MWRNXTR003", "MWGNXTR003", "MWMNXTR003", "MWLNXTR003"],
        ["MWXNXTR003", "VWGNXTR001", "VWLNXTR001"],
    )
    prep_category = "mic"
    sign = "PG"
    activate = False
    inactivate = False
    active_mic_apps_from_start = base_store.applications(
        category=prep_category, archived=False
    ).count()
    inactive_mic_apps_from_start = base_store.applications(
        category=prep_category, archived=True
    ).count()

    # WHEN syncing app-tags in that orderform
    import_apptags(
        store=base_store,
        excel_path=microbial_orderform,
        prep_category=prep_category,
        sign=sign,
        activate=activate,
        inactivate=inactivate,
        sheet_name="Drop down list",
        tag_column=2,
    )

    # THEN same number of active and inactive mic applications in status database
    active_mic_apps_after_when = base_store.applications(
        category=prep_category, archived=False
    ).count()
    inactive_mic_apps_after_when = base_store.applications(
        category=prep_category, archived=True
    ).count()
    assert active_mic_apps_from_start == active_mic_apps_after_when
    assert inactive_mic_apps_from_start == inactive_mic_apps_after_when


def test_sync_microbial_orderform_activate(base_store: Store, microbial_orderform):
    # GIVEN a microbial orderform and a store where all the apptags exists half some inactive and
    # some active
    ensure_applications(
        base_store,
        ["MWRNXTR003", "MWGNXTR003", "MWMNXTR003", "MWLNXTR003"],
        ["MWXNXTR003", "VWGNXTR001", "VWLNXTR001"],
    )
    prep_category = "mic"
    sign = "PG"
    activate = True
    inactivate = False
    active_mic_apps_from_start = base_store.applications(
        category=prep_category, archived=False
    ).count()
    inactive_mic_apps_from_start = base_store.applications(
        category=prep_category, archived=True
    ).count()

    # WHEN syncing app-tags in that orderform
    import_apptags(
        store=base_store,
        excel_path=microbial_orderform,
        prep_category=prep_category,
        sign=sign,
        activate=activate,
        inactivate=inactivate,
        sheet_name="Drop down list",
        tag_column=2,
    )

    # THEN more active mic applications in status database and same inactive
    active_mic_apps_after_when = base_store.applications(
        category=prep_category, archived=False
    ).count()
    inactive_mic_apps_after_when = base_store.applications(
        category=prep_category, archived=True
    ).count()
    assert active_mic_apps_from_start < active_mic_apps_after_when
    assert inactive_mic_apps_from_start > inactive_mic_apps_after_when


def test_sync_microbial_orderform_inactivate(base_store: Store, microbial_orderform):
    # GIVEN a microbial orderform and a store where all the apptags exists half some inactive and
    # some active
    ensure_applications(
        base_store,
        ["MWRNXTR003", "MWGNXTR003", "MWMNXTR003", "MWLNXTR003", "dummy_tag"],
        ["MWXNXTR003", "VWGNXTR001", "VWLNXTR001"],
    )
    prep_category = "mic"
    sign = "PG"
    activate = False
    inactivate = True
    active_mic_apps_from_start = base_store.applications(
        category=prep_category, archived=False
    ).count()
    inactive_mic_apps_from_start = base_store.applications(
        category=prep_category, archived=True
    ).count()

    # WHEN syncing app-tags in that orderform
    import_apptags(
        store=base_store,
        excel_path=microbial_orderform,
        prep_category=prep_category,
        sign=sign,
        activate=activate,
        inactivate=inactivate,
        sheet_name="Drop down list",
        tag_column=2,
    )

    # THEN same number of active and more inactive mic applications in status database
    active_mic_apps_after_when = base_store.applications(
        category=prep_category, archived=False
    ).count()
    inactive_mic_apps_after_when = base_store.applications(
        category=prep_category, archived=True
    ).count()
    assert active_mic_apps_from_start > active_mic_apps_after_when
    assert inactive_mic_apps_from_start < inactive_mic_apps_after_when


def ensure_applications(base_store: Store, active_applications: list, inactive_applications: list):
    """Create some requested applications for the tests """
    for active_application in active_applications:
        if not base_store.application(active_application):
            base_store.add_commit(
                base_store.add_application(
                    active_application,
                    "mic",
                    "dummy_description",
                    is_archived=False,
                    percent_kth=80,
                )
            )

    for inactive_application in inactive_applications:
        if not base_store.application(inactive_application):
            base_store.add_commit(
                base_store.add_application(
                    inactive_application,
                    category="mic",
                    description="dummy_description",
                    is_archived=True,
                    percent_kth=80,
                )
            )


def ensure_application(store, tag):
    """Ensure that the specified application exists in the store"""
    application = store.application(tag=tag)
    if not application:
        application = store.add_application(
            tag=tag,
            category="wgs",
            description="dummy_description",
            is_external=False,
            percent_kth=80,
        )
        store.add_commit(application)

    return application


def add_applications(store, application_versions_file):
    """Ensure all applications in the xl exists"""

    raw_versions = XlFileHelper.get_raw_dicts_from_xl(application_versions_file)

    for raw_version in raw_versions:
        tag = _get_tag_from_raw_version(raw_version)
        ensure_application(store, tag)


def get_prices_from_store(store, raw_price):
    """Gets all versions for the specified application"""
    tag = _get_tag_from_raw_version(raw_price)
    return store.application(tag).versions


def get_application_from_store(store, raw_application):
    """Gets the specified application"""
    tag = _get_tag_from_raw_application(raw_application)
    return store.application(tag)


def exists_version_in_store(raw_price, store, datemode):
    """Check if the given raw version exists in the store"""
    db_versions = get_prices_from_store(store, raw_price)

    version_found = False
    for db_price in db_versions:
        if versions_are_same(db_price, raw_price, datemode):
            version_found = True

    return version_found


def all_versions_exists_in_store(store, excel_path):
    """Check if all versions in the excel exists in the store"""
    raw_versions = XlFileHelper.get_raw_dicts_from_xl(excel_path)
    datemode = XlFileHelper.get_datemode_from_xl(excel_path)
    for raw_version in raw_versions:
        if not exists_version_in_store(raw_version, store, datemode):
            return False

    return True


def all_applications_exists(store, applications_file):
    """Check if all applications in the excel exists in the store"""
    raw_applications = XlFileHelper.get_raw_dicts_from_xl(applications_file)

    for raw_application in raw_applications:
        if not exists_application_in_store(raw_application, store):
            return False

    return True


def exists_application_in_store(raw_application, store):
    """Check if the given raw application exists in the store"""
    db_application = get_application_from_store(store, raw_application)

    return db_application is not None

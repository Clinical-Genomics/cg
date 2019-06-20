"""Tests for reset part of the store API"""

from cg.store import Store
from cg.store.api.import_func import prices_are_same, versions_are_same, \
    import_application_versions, get_raw_data_from_xl, get_tag_from_raw_version, \
    add_version_from_raw, get_workbook_from_xl, import_applications, get_datemode_from_xl, \
    get_tag_from_raw_application


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
    raw_version = get_raw_data_from_xl(application_versions_file)[0]
    tag = get_tag_from_raw_version(raw_version)
    application_obj = store.application(tag)
    sign = 'DummySign'
    workbook = get_workbook_from_xl(application_versions_file)
    db_version = add_version_from_raw(application_obj, None, raw_version,
                                      sign, store, workbook)
    datemode = get_datemode_from_xl(application_versions_file)

    # WHEN calling versions are same
    should_be_same = versions_are_same(db_version, raw_version, datemode)

    # THEN versions are considered same
    assert should_be_same


def test_versions_are_not_same(store, application_versions_file):
    # GIVEN an excel price row
    # NOT same price row committed to the database
    add_applications(store, application_versions_file)
    raw_version = get_raw_data_from_xl(application_versions_file)[0]
    tag = get_tag_from_raw_version(raw_version)
    application_obj = store.application(tag)
    sign = 'DummySign'
    workbook = get_workbook_from_xl(application_versions_file)
    db_version = add_version_from_raw(application_obj, None, raw_version,
                                      sign, store, workbook)
    datemode = get_datemode_from_xl(application_versions_file)
    another_raw_version = get_raw_data_from_xl(application_versions_file)[1]

    # WHEN calling versions are same
    should_not_be_same = versions_are_same(db_version, another_raw_version, datemode)

    # THEN versions are not considered same
    assert not should_not_be_same


def test_application_version(application_versions_file, store: Store):
    # GIVEN a store with applications
    # and an excel file with prices for those applications
    add_applications(store, application_versions_file)
    sign = 'TestSign'

    # WHEN calling import_application_version
    import_application_versions(store, application_versions_file, sign)

    # THEN versions should have been created in the store
    assert all_versions_exists_in_store(store, application_versions_file)


def test_application(applications_file, store: Store):
    # GIVEN a store and an excel file with applications
    sign = 'TestSign'

    # WHEN calling versions are same
    import_applications(store, applications_file, sign)

    # THEN applications should have been created in the store
    assert all_applications_exists(store, applications_file)


def ensure_application(store, tag):
    """Ensure that the specified application exists in the store"""
    application = store.application(tag=tag)
    if not application:
        application = store.add_application(tag=tag, category='wgs',
                                            description='dummy_description',
                                            is_external=False)
        store.add_commit(application)

    return application


def add_applications(store, application_versions_file):
    """Ensure all applications in the xl exists"""

    raw_versions = get_raw_data_from_xl(application_versions_file)

    for raw_version in raw_versions:
        tag = get_tag_from_raw_version(raw_version)
        ensure_application(store, tag)


def get_prices_from_store(store, raw_price):
    """Gets all versions for the specified application"""
    tag = get_tag_from_raw_version(raw_price)
    return store.application(tag).versions


def get_application_from_store(store, raw_application):
    """Gets the specified application"""
    tag = get_tag_from_raw_application(raw_application)
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
    raw_versions = get_raw_data_from_xl(excel_path)
    datemode = get_datemode_from_xl(excel_path)
    for raw_version in raw_versions:
        if not exists_version_in_store(raw_version, store, datemode):
            return False

    return True


def all_applications_exists(store, applications_file):
    """Check if all applications in the excel exists in the store"""
    raw_applications = get_raw_data_from_xl(applications_file)

    for raw_application in raw_applications:
        if not exists_application_in_store(raw_application, store):
            return False

    return True


def exists_application_in_store(raw_application, store):
    """Check if the given raw application exists in the store"""
    db_application = get_application_from_store(store, raw_application)

    return db_application is not None

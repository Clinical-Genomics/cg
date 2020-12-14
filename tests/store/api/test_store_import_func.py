"""Tests for reset part of the store API"""

from typing import List, Iterable

from openpyxl.workbook import Workbook

from cg.store import Store, models
from cg.store.api.import_func import (
    prices_are_same,
    versions_are_same,
    add_application_version,
    import_application_versions,
    _get_tag_from_raw_version,
    import_applications,
    import_apptags,
    XlFileHelper,
    parse_applications,
    parse_application_versions,
)
from cg.store.api.models import ApplicationVersionSchema, ApplicationSchema


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


def test_versions_are_same(applications_store: Store, application_versions_file: str):
    # GIVEN a database with some applications loaded
    store = applications_store

    # GIVEN an excel price row
    # same price row committed to the database
    excel_versions: List[ApplicationVersionSchema] = list(
        parse_application_versions(excel_path=application_versions_file)
    )
    version: ApplicationVersionSchema = excel_versions[0]

    # GIVEN that the application exists in the database
    application_obj: models.Application = store.application(version.app_tag)

    # GIVEN that there is a application version
    sign = "DummySign"
    db_version: models.ApplicationVersion = add_application_version(
        application_obj=application_obj,
        latest_version=None,
        version=version,
        sign=sign,
        store=store,
    )

    # WHEN calling versions are same
    should_be_same = versions_are_same(version_obj=db_version, application_version=version)

    # THEN versions are considered same
    assert should_be_same


def test_versions_are_not_same(applications_store: Store, application_versions_file: str):
    # GIVEN a database with some applications loaded
    store = applications_store
    # GIVEN an excel price row
    # NOT same price row committed to the database
    excel_versions: List[ApplicationVersionSchema] = list(
        parse_application_versions(excel_path=application_versions_file)
    )
    version: ApplicationVersionSchema = excel_versions[0]
    application_obj: models.Application = store.application(version.app_tag)
    sign = "DummySign"

    db_version: models.ApplicationVersion = add_application_version(
        application_obj=application_obj,
        latest_version=None,
        version=version,
        sign=sign,
        store=store,
    )

    another_version: ApplicationVersionSchema = excel_versions[1]

    # WHEN calling versions are same
    should_not_be_same: bool = versions_are_same(
        version_obj=db_version, application_version=another_version
    )

    # THEN versions are not considered same
    assert should_not_be_same is False


def test_application_version(
    applications_store: Store, application_versions_file: str, store: Store
):
    # GIVEN a store with applications
    # and an excel file with prices for those applications
    sign = "TestSign"

    # WHEN calling import_application_version
    import_application_versions(
        store=applications_store,
        excel_path=application_versions_file,
        sign=sign,
        dry_run=False,
        skip_missing=False,
    )

    # THEN versions should have been created in the store
    assert all_versions_exists_in_store(
        store=applications_store, excel_path=application_versions_file
    )


def test_application_version_dry_run(applications_store: Store, application_versions_file: str):
    # GIVEN a store with applications
    # and an excel file with prices for those applications
    sign = "TestSign"

    # WHEN calling import_application_version as dry run
    import_application_versions(
        store=applications_store,
        excel_path=application_versions_file,
        sign=sign,
        dry_run=True,
        skip_missing=False,
    )

    # THEN versions should not have been created in the store
    assert not all_versions_exists_in_store(
        store=applications_store, excel_path=application_versions_file
    )


def test_application(store: Store, applications_file: str):
    # GIVEN an excel file with applications
    assert all_applications_exists(store, applications_file) is False
    # GIVEN a store without the applications
    sign = "TestSign"

    # WHEN calling import_applications
    import_applications(store=store, excel_path=applications_file, sign=sign, dry_run=False)

    # THEN applications should have been created in the store
    assert all_applications_exists(store, applications_file)


def test_application_sheet_name(applications_file: str, store: Store):
    # GIVEN a store and an excel file with applications
    sign = "TestSign"

    # WHEN calling import_applications
    import_applications(
        store=store,
        excel_path=applications_file,
        sign=sign,
        dry_run=False,
        sheet_name="application",
    )

    # THEN applications should have been created in the store
    assert all_applications_exists(store, applications_file)


def test_application_dry_run(applications_file: str, store: Store):
    # GIVEN a store and an excel file with applications
    sign = "TestSign"

    # WHEN calling import_applications as dry run
    import_applications(store=store, excel_path=applications_file, sign=sign, dry_run=True)

    # THEN applications should not have been created in the store
    assert not all_applications_exists(store, applications_file)


def test_sync_microbial_orderform_dry_run(microbial_store: Store, microbial_orderform: str):
    # GIVEN a microbial orderform and a store where all the apptags exists half some inactive and
    # some active
    prep_category = "mic"
    sign = "PG"
    activate = False
    inactivate = False
    active_mic_apps_from_start = microbial_store.applications(
        category=prep_category, archived=False
    ).count()
    inactive_mic_apps_from_start = microbial_store.applications(
        category=prep_category, archived=True
    ).count()

    # WHEN syncing app-tags in that orderform
    import_apptags(
        store=microbial_store,
        excel_path=microbial_orderform,
        prep_category=prep_category,
        sign=sign,
        activate=activate,
        inactivate=inactivate,
        sheet_name="Drop down list",
        tag_column=2,
    )

    # THEN same number of active and inactive mic applications in status database
    active_mic_apps_after_when = microbial_store.applications(
        category=prep_category, archived=False
    ).count()
    inactive_mic_apps_after_when = microbial_store.applications(
        category=prep_category, archived=True
    ).count()
    assert active_mic_apps_from_start == active_mic_apps_after_when
    assert inactive_mic_apps_from_start == inactive_mic_apps_after_when


def test_sync_microbial_orderform_activate(microbial_store: Store, microbial_orderform):
    # GIVEN a microbial orderform and a store where all the apptags exists half some inactive and
    # some active
    prep_category = "mic"
    sign = "PG"
    activate = True
    inactivate = False
    active_mic_apps_from_start = microbial_store.applications(
        category=prep_category, archived=False
    ).count()
    inactive_mic_apps_from_start = microbial_store.applications(
        category=prep_category, archived=True
    ).count()

    # WHEN syncing app-tags in that orderform
    import_apptags(
        store=microbial_store,
        excel_path=microbial_orderform,
        prep_category=prep_category,
        sign=sign,
        activate=activate,
        inactivate=inactivate,
        sheet_name="Drop down list",
        tag_column=2,
    )

    # THEN more active mic applications in status database and same inactive
    active_mic_apps_after_when = microbial_store.applications(
        category=prep_category, archived=False
    ).count()
    inactive_mic_apps_after_when = microbial_store.applications(
        category=prep_category, archived=True
    ).count()
    assert active_mic_apps_from_start < active_mic_apps_after_when
    assert inactive_mic_apps_from_start > inactive_mic_apps_after_when


def test_sync_microbial_orderform_inactivate(microbial_store_dummy_tag: Store, microbial_orderform):
    # GIVEN a microbial orderform and a store where all the apptags exists half some inactive and
    # some active
    prep_category = "mic"
    sign = "PG"
    activate = False
    inactivate = True
    active_mic_apps_from_start = microbial_store_dummy_tag.applications(
        category=prep_category, archived=False
    ).count()
    inactive_mic_apps_from_start = microbial_store_dummy_tag.applications(
        category=prep_category, archived=True
    ).count()

    # WHEN syncing app-tags in that orderform
    import_apptags(
        store=microbial_store_dummy_tag,
        excel_path=microbial_orderform,
        prep_category=prep_category,
        sign=sign,
        activate=activate,
        inactivate=inactivate,
        sheet_name="Drop down list",
        tag_column=2,
    )

    # THEN same number of active and more inactive mic applications in status database
    active_mic_apps_after_when = microbial_store_dummy_tag.applications(
        category=prep_category, archived=False
    ).count()
    inactive_mic_apps_after_when = microbial_store_dummy_tag.applications(
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
                    percent_reads_guaranteed=75,
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
                    percent_reads_guaranteed=75,
                )
            )


def ensure_application(store: Store, tag: str):
    """Ensure that the specified application exists in the store"""
    application = store.application(tag=tag)
    if not application:
        application = store.add_application(
            tag=tag,
            category="wgs",
            description="dummy_description",
            is_external=False,
            percent_kth=80,
            percent_reads_guaranteed=75,
        )
        store.add_commit(application)

    return application


def add_applications(store, application_versions_file):
    """Ensure all applications in the xl exists"""

    raw_versions = XlFileHelper.get_raw_dicts_from_xl(application_versions_file)

    for raw_version in raw_versions:
        tag = _get_tag_from_raw_version(raw_version)
        ensure_application(store, tag)


def get_versions_from_store(store: Store, application_tag: str) -> List[models.ApplicationVersion]:
    """Gets all versions for the specified application"""

    return store.application(application_tag).versions


def get_application_from_store(store: Store, application_tag: str) -> models.Application:
    """Gets the specified application"""

    return store.application(application_tag)


def exists_version_in_store(store: Store, application: ApplicationVersionSchema):
    """Check if the given raw version exists in the store"""
    db_versions: List[models.Application] = get_versions_from_store(
        store=store, application_tag=application.app_tag
    )

    for db_version in db_versions:
        if versions_are_same(version_obj=db_version, application_version=application):
            return True

    return False


def all_versions_exists_in_store(store: Store, excel_path: str):
    """Check if all versions in the excel exists in the store"""
    applications: Iterable[ApplicationVersionSchema] = parse_application_versions(
        excel_path=excel_path
    )

    for application in applications:
        if not exists_version_in_store(store=store, application=application):
            return False

    return True


def all_applications_exists(store: Store, applications_file: str):
    """Check if all applications in the excel exists in the store"""
    applications: Iterable[ApplicationSchema] = parse_applications(excel_path=applications_file)

    for application in applications:
        if not exists_application_in_store(store=store, application_tag=application.tag):
            return False

    return True


def exists_application_in_store(store: Store, application_tag: str):
    """Check if the given raw application exists in the store"""
    db_application = get_application_from_store(store=store, application_tag=application_tag)

    return db_application is not None

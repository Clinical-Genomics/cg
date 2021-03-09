"""Tests for reset part of the store API"""

from typing import List

from cg.store import Store, models
from cg.store.api.import_func import (
    add_application_version,
    import_application_versions,
    import_applications,
    import_apptags,
    parse_application_versions,
    prices_are_same,
    versions_are_same,
)
from cg.store.api.models import ApplicationVersionSchema
from tests.store.api.conftest import StoreCheckers
from tests.store_helpers import StoreHelpers


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

    # GIVEN an excel price row
    # NOT same price row committed to the database
    excel_versions: List[ApplicationVersionSchema] = list(
        parse_application_versions(excel_path=application_versions_file)
    )
    version: ApplicationVersionSchema = excel_versions[0]
    application_obj: models.Application = applications_store.application(version.app_tag)
    sign = "DummySign"

    db_version: models.ApplicationVersion = add_application_version(
        application_obj=application_obj,
        latest_version=None,
        version=version,
        sign=sign,
        store=applications_store,
    )

    another_version: ApplicationVersionSchema = excel_versions[1]

    # WHEN calling versions are same
    should_not_be_same: bool = versions_are_same(
        version_obj=db_version, application_version=another_version
    )

    # THEN versions are not considered same
    assert should_not_be_same is False


def test_application_version(
    applications_store: Store,
    application_versions_file: str,
    store: Store,
    store_checkers: StoreCheckers,
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
    assert store_checkers.all_versions_exist_in_store(
        store=applications_store, excel_path=application_versions_file
    )


def test_application_version_dry_run(
    applications_store: Store, application_versions_file: str, store_checkers: StoreCheckers
):
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
    assert not store_checkers.all_versions_exist_in_store(
        store=applications_store, excel_path=application_versions_file
    )


def test_application(store: Store, applications_file: str, store_checkers: StoreCheckers):
    # GIVEN an excel file with applications
    assert store_checkers.all_applications_exists(store, applications_file) is False
    # GIVEN a store without the applications
    sign = "TestSign"

    # WHEN calling import_applications
    import_applications(store=store, excel_path=applications_file, sign=sign, dry_run=False)

    # THEN applications should have been created in the store
    assert store_checkers.all_applications_exists(store, applications_file)


def test_application_sheet_name(
    applications_file: str, store: Store, store_checkers: StoreCheckers
):
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
    assert store_checkers.all_applications_exists(store, applications_file)


def test_application_dry_run(applications_file: str, store: Store, store_checkers: StoreCheckers):
    # GIVEN a store and an excel file with applications
    sign = "TestSign"

    # WHEN calling import_applications as dry run
    import_applications(store=store, excel_path=applications_file, sign=sign, dry_run=True)

    # THEN applications should not have been created in the store
    assert not store_checkers.all_applications_exists(store, applications_file)


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
        signature=sign,
        activate=activate,
        inactivate=inactivate,
        sheet_name="Drop down list",
        tag_column=2,
        tag_row=1,
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


def test_sync_microbial_orderform_activate(microbial_store: Store, microbial_orderform: str):
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
        signature=sign,
        activate=activate,
        inactivate=inactivate,
        sheet_name="Drop down list",
        tag_column=2,
        tag_row=1,
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


def test_sync_rml_orderform_inactivate(rml_store: Store, rml_orderform: str, helpers: StoreHelpers):
    # GIVEN a rml orderform and a store where all the apptags exists half some inactive and
    # some active
    prep_category = "rml"
    sign = "PG"
    activate = False
    inactivate = True

    helpers.add_application(
        store=rml_store,
        application_tag="apptag_to_inactivate",
        is_archived=False,
        application_type=prep_category,
    )
    active_apps_from_start = rml_store.applications(category=prep_category, archived=False).count()
    inactive_apps_from_start = rml_store.applications(category=prep_category, archived=True).count()

    # WHEN syncing app-tags in that orderform
    import_apptags(
        store=rml_store,
        excel_path=rml_orderform,
        prep_category=prep_category,
        signature=sign,
        activate=activate,
        inactivate=inactivate,
        sheet_name="Drop down list",
        tag_column=7,
        tag_row=0,
    )

    # THEN the number of active should be less and the number of inactive more than before
    active_apps_after_when = rml_store.applications(category=prep_category, archived=False).count()
    inactive_apps_after_when = rml_store.applications(category=prep_category, archived=True).count()
    assert active_apps_from_start > active_apps_after_when
    assert inactive_apps_from_start < inactive_apps_after_when

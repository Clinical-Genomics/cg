"""Import functionality"""

import logging
import sys
from datetime import datetime

import xlrd
from cg.exc import CgError
from cg.store import models, Store


def import_application_versions(store, excel_path, sign, dry_run, skip_missing):
    """
    Imports all application versions from the specified excel file
    Args:
        :param store:               Status database store
        :param excel_path:          Path to excel file with headers: 'App tag', 'Valid from',
                                    'Standard', 'Priority', 'Express', 'Research'
        :param sign:                Signature of user running the script
        :param dry_run:             Test run, no changes to the database
        :param skip_missing:        Continue despite missing applications
    """

    workbook = XlFileHelper.get_workbook_from_xl(excel_path)
    raw_versions = XlFileHelper.get_raw_dicts_from_xl(excel_path)

    for raw_version in raw_versions:
        tag = _get_tag_from_raw_version(raw_version)
        application_obj = store.application(tag)

        if not application_obj:
            logging.error("Failed to find application! Please manually " "add application: %s", tag)

            if skip_missing:
                continue

            logging.error("Rolling back transaction.")
            store.rollback()
            sys.exit()

        app_tag = application_obj.tag
        latest_version = store.latest_version(tag)

        if latest_version and versions_are_same(latest_version, raw_version, workbook.datemode):
            logging.info("skipping redundant application version for app tag %s", app_tag)
            continue

        logging.info("adding new application version to transaction for app tag %s", app_tag)
        new_version = add_version_from_raw(
            application_obj, latest_version, raw_version, sign, store, workbook
        )
        store.add(new_version)

    if not dry_run:
        logging.info(
            "all application versions successfully added to transaction, committing " "transaction"
        )
        store.commit()
    else:
        logging.error("Dry-run, rolling back transaction.")
        store.rollback()


def import_applications(store, excel_path, sign, dry_run, sheet_name=None):
    """
    Imports all applications from the specified excel file
    Args:
        :param sheet_name:          Optional sheet name
        :param store:               status database store
        :param excel_path:          Path to excel file with headers: 'App tag', 'Valid from',
                                    'Standard', 'Priority', 'Express', 'Research'
        :param sign:                Signature of user running the script
        :param dry_run:             Test run, no changes to the database
    """

    raw_applications = XlFileHelper.get_raw_dicts_from_xl(excel_path, sheet_name)

    for raw_application in raw_applications:
        tag = _get_tag_from_raw_application(raw_application)
        application_obj = store.application(tag)

        if application_obj and applications_are_same(application_obj, raw_application):
            logging.info("skipping redundant application %s", tag)
            continue

        logging.info("adding new application to transaction %s", tag)
        new_application = add_application_from_raw(raw_application, sign, store)
        store.add(new_application)

    if not dry_run:
        logging.info("all applications successfully added to transaction, committing transaction")
        store.commit()
    else:
        logging.error("Dry-run, rolling back transaction.")
        store.rollback()


def prices_are_same(first_price, second_price):
    """Checks if the given prices are to be considered equal"""

    if first_price == second_price:
        return True
    if first_price and second_price:
        return int(round(float(first_price))) == int(round(float(second_price)))

    return False


def versions_are_same(version_obj: models.ApplicationVersion, raw_version: dict, datemode: int):
    """Checks if the given versions are to be considered equal"""

    return (
        version_obj.application.tag == _get_tag_from_raw_version(raw_version)
        and version_obj.valid_from
        == datetime(*xlrd.xldate_as_tuple(float(raw_version["Valid from"]), datemode))
        and prices_are_same(version_obj.price_standard, raw_version["Standard"])
        and prices_are_same(version_obj.price_priority, raw_version["Priority"])
        and prices_are_same(version_obj.price_express, raw_version["Express"])
        and prices_are_same(version_obj.price_research, raw_version["Research"])
    )


def applications_are_same(application_obj: models.Application, raw_application: dict):
    """Checks if the given applications are to be considered equal"""

    return application_obj and application_obj.tag == _get_tag_from_raw_application(raw_application)


def add_version_from_raw(
    application_obj, latest_version, raw_version, sign, store: Store, workbook
):
    """Adds an application version from a raw application version record"""
    new_version = store.add_version(
        application=application_obj,
        version=latest_version.version + 1 if latest_version else 1,
        valid_from=datetime(
            *xlrd.xldate_as_tuple(float(raw_version["Valid from"]), workbook.datemode)
        ),
        prices={
            "standard": raw_version["Standard"],
            "priority": raw_version["Priority"],
            "express": raw_version["Express"],
            "research": raw_version["Research"],
        },
        comment="Added by %s" % sign,
    )
    return new_version


def add_application_from_raw(raw_application, sign, store: Store):
    """Adds an application from a raw application record"""
    new_application = store.add_application(
        tag=_get_tag_from_raw_application(raw_application),
        category=raw_application["prep_category"],
        description=raw_application["description"],
        is_accredited=raw_application["is_accredited"] == 1.0,
        turnaround_time=raw_application["turnaround_time"],
        minimum_order=raw_application["minimum_order"],
        sequencing_depth=raw_application["sequencing_depth"],
        target_reads=raw_application["target_reads"],
        sample_amount=raw_application["sample_amount"],
        sample_volume=raw_application["sample_volume"],
        sample_concentration=raw_application["sample_concentration"],
        priority_processing=raw_application["priority_processing"] == 1.0,
        details=raw_application["details"],
        limitations=raw_application["limitations"],
        percent_kth=raw_application["percent_kth"],
        comment=raw_application["comment"] + " Added by %s" % sign,
        is_archived=raw_application["is_archived"] == 1.0,
        is_external=raw_application["is_external"] == 1.0,
        created_at=datetime.now(),
    )
    return new_application


def import_apptags(
    store: Store,
    excel_path: str,
    prep_category: str,
    sign: str,
    sheet_name: str,
    tag_column: int,
    activate: bool,
    inactivate: bool,
):
    """Syncs all applications from the specified excel file"""

    orderform_application_tags = []

    for raw_row in XlFileHelper.get_raw_cells_from_xl(excel_path, sheet_name, tag_column):
        tag = _get_tag_from_column(raw_row, tag_column)
        logging.info("Found: %s in orderform", tag)
        orderform_application_tags.append(tag)

    if not orderform_application_tags:
        message = "No applications found in column %s (zero-based), exiting" % tag_column
        raise CgError(message)

    for orderform_application_tag in orderform_application_tags:
        application_obj = store.application(tag=orderform_application_tag)

        if not application_obj:
            message = "Application %s was not found" % orderform_application_tag
            raise CgError(message)

        if application_obj.prep_category != prep_category:
            message = "%s prep_category, expected: %s was: %s" % (
                orderform_application_tag,
                prep_category,
                application_obj.prep_category,
            )
            raise CgError(message)

        if application_obj.is_archived:
            if activate:
                application_obj.comment = (
                    f"{application_obj.comment}\n{str(datetime.now())[:-10]}"
                    f"Application un-archived by {sign}"
                )
                application_obj.is_archived = False
                logging.info("Un-archiving %s", application_obj)
            else:
                logging.warning(
                    "%s is marked as archived but is used in the orderform, consider "
                    "activating it",
                    application_obj,
                )
        else:
            logging.info("%s is already active, no need to activate it", application_obj)

    all_active_apps_for_category = store.applications(category=prep_category, archived=False)

    for active_application in all_active_apps_for_category:
        if active_application.tag not in orderform_application_tags:
            if inactivate:
                active_application.is_archived = True
                active_application.comment = (
                    f"{active_application.comment}"
                    f"\n{str(datetime.now())[:-10]} "
                    f"Application archived by {sign}"
                )
                logging.info("Archiving %s", active_application)
            else:
                logging.warning(
                    "%s is marked as active but is not used in the orderform, "
                    "consider archiving it",
                    active_application,
                )
        else:
            logging.info(
                "%s was found in orderform tags, no need to archive it", active_application
            )

    if not activate and not inactivate:
        logging.info("no change mode requested, rolling back transaction")
        store.rollback()
    else:
        logging.info("all applications successfully synced, committing transaction")
        store.commit()


class XlFileHelper:
    """Organises methods to get data from file"""

    @staticmethod
    def get_raw_dicts_from_xl(excel_path, sheet_name=None):
        """Get raw data from the xl file"""
        workbook = XlFileHelper.get_workbook_from_xl(excel_path)
        if sheet_name:
            data_sheet = workbook.sheet_by_name(sheet_name)
        else:
            data_sheet = workbook.sheet_by_index(0)
        return XlSheetHelper.get_raw_dicts_from_xlsheet(data_sheet)

    @staticmethod
    def get_raw_cells_from_xl(excel_path, sheet_name, tag_column):
        """Get raw data from the xl file"""
        workbook = XlFileHelper.get_workbook_from_xl(excel_path)
        data_sheet = workbook.sheet_by_name(sheet_name)
        return XlSheetHelper.get_raw_cells_from_sheet(data_sheet, tag_column)

    @staticmethod
    def get_workbook_from_xl(excel_path):
        """Get the workbook from the xl file"""
        return xlrd.open_workbook(excel_path)

    @staticmethod
    def get_datemode_from_xl(excel_path):
        """"Returns the datemode of of the workbook in the specified xl"""
        workbook = xlrd.open_workbook(excel_path)
        return workbook.datemode


class XlSheetHelper:
    """Organises methods to get data from sheet"""

    @staticmethod
    def get_raw_dicts_from_xlsheet(sheet) -> []:
        """Get the relevant rows from a sheet."""
        raw_data = []
        header_row = []
        first_row = True

        for row in sheet.get_rows():
            if row[0].value == "":
                break

            if first_row:
                header_row = [cell.value for cell in row]
                first_row = False
            else:
                values = [str(cell.value) for cell in row]
                version_dict = dict(zip(header_row, values))
                raw_data.append(version_dict)

        return raw_data

    @staticmethod
    def no_more_tags(row, tag_column: int) -> bool:
        """Returns if there are no more app-tags found"""
        return _get_tag_from_column(row, tag_column).value == ""

    @staticmethod
    def get_raw_cells_from_sheet(sheet, tag_column: int) -> []:
        """Get the relevant rows from an price sheet."""
        raw_data = []

        for row in sheet.get_rows():
            if XlSheetHelper.no_more_tags(row, tag_column):
                break

            values = [str(cell.value) for cell in row]
            raw_data.append(values)

        return raw_data


def _get_tag_from_raw_version(raw_data):
    """Gets the application tag from a raw xl application version record"""
    return raw_data["App tag"]


def _get_tag_from_column(raw_data, column: int):
    """Gets the application tag from a raw xl data record"""
    return raw_data[column]


def _get_tag_from_raw_application(raw_application):
    """Gets the application tag from a raw xl application record"""
    return raw_application["tag"]

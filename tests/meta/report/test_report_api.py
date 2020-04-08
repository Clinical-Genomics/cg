import os
from pathlib import Path

import pytest
from cg.meta.report.api import ReportAPI


def test_init():
    ReportAPI(
        lims_api="lims",
        store="analysis_store",
        chanjo_api="chanjo",
        analysis_api="analysis",
        scout_api="scout",
    )


def test_collect_delivery_data(report_api, report_store):
    # GIVEN an initialised report_api and a family ready for delivery report creation

    # WHEN collecting delivery data for a certain
    family_id = "yellowhog"
    family = report_store.family(family_id)
    assert family
    assert family.links
    assert family.analyses
    delivery_data = report_api._get_delivery_data(family_id=family_id)

    # THEN all data for the delivery report should have been collected
    assert delivery_data["report_version"]
    assert delivery_data["previous_report_version"]
    assert delivery_data["family"]
    assert delivery_data["customer_name"]
    assert delivery_data["today"]
    assert delivery_data["panels"]

    assert delivery_data["customer_invoice_address"]
    assert delivery_data["customer_name"]
    assert delivery_data["scout_access"]
    assert delivery_data["accredited"]

    for application in delivery_data["applications"]:
        assert application["tag"]
        assert application["description"]
        assert application["limitations"]

    assert delivery_data["samples"]

    for sample in delivery_data["samples"]:
        assert sample["name"]
        assert sample["internal_id"]
        assert sample["sex"]
        assert sample["status"]
        assert sample["source"]
        assert sample["ticket"]
        assert sample["application"]
        assert sample["received_at"]

        assert sample["ordered_at"]
        assert sample["prep_method"]
        assert sample["prepared_at"]
        assert sample["capture_kit"]
        assert sample["sequencing_method"]
        assert sample["sequenced_at"]
        assert sample["delivery_method"]
        assert sample["delivered_at"]

        assert sample["million_read_pairs"]
        assert sample["mapped_reads"]
        assert sample["target_coverage"]
        assert sample["target_completeness"]
        assert sample["duplicates"]
        assert sample["processing_time"]
        assert sample["data_analysis"]
        assert sample["analysis_sex"]

    assert delivery_data["pipeline_version"]
    assert delivery_data["genome_build"]


def test_get_status_from_status_db(report_api):
    # GIVEN data from an analysed case and an initialised report_api

    # WHEN fetch_application_data_from_status_db
    samples = report_api._fetch_family_samples_from_status_db("yellowhog")

    # THEN
    # the samples contain a status
    for sample in samples:
        assert sample["status"]


def test_incorporate_lims_methods(report_samples, report_api):
    # GIVEN data from an analysed case and an initialised report_api

    # WHEN fetch_and_add_lims_methods
    samples = report_samples
    report_api._incorporate_lims_methods(samples)

    # THEN certain metrics should have been calculated

    # each sample has a property library_prep_method with a value
    for sample in samples:
        assert sample["prep_method"]

    # each sample has a property sequencing_method with a value
    for sample in samples:
        assert sample["sequencing_method"]

    # each sample has a property delivery_method with a value
    for sample in samples:
        assert sample["delivery_method"]


def test_render_delivery_report(report_api):
    # GIVEN proper qc data from an analysis exist
    report_data = report_api._get_delivery_data(family_id="yellowhog")

    # WHEN rendering a report from that data
    rendered_report = ReportAPI._render_delivery_report(report_data)

    # THEN a html report with certain data should have been rendered
    assert len(rendered_report) > 0


def test_create_delivery_report(report_api):
    # GIVEN initialized ReportAPI

    # WHEN rendering a report from that data
    created_report = report_api.create_delivery_report(family_id="yellowhog")

    # THEN a html report with certain data should have been rendered
    assert len(created_report) > 0


def test_create_delivery_report_file(report_api: ReportAPI):
    # GIVEN initialized ReportAPI

    # WHEN rendering a report from that data
    created_report_file = report_api.create_delivery_report_file(
        family_id="yellowhog", file_path=Path(".")
    )

    # THEN a html report with certain data should have been created on disk
    assert os.path.isfile(created_report_file.name)
    os.unlink(created_report_file.name)


def test_incorporate_coverage_data(report_api, report_samples):
    # GIVEN an initialised report_api and the chanjo_api does not return what we want
    report_api.chanjo._sample_coverage_returns_none = True
    samples = report_samples

    # WHEN failing to get latest trending data for a family
    report_api._incorporate_coverage_data(samples=samples, panels="dummyPanel")

    # THEN there should be a log entry about this
    for sample in samples:
        lims_id = sample["id"]
        assert not sample.get("target_coverage")
        assert not sample.get("target_completeness")
        lims_id_found_in_warnings = False
        for warning in report_api.log.get_warnings():
            lims_id_found_in_warnings = lims_id in warning or lims_id_found_in_warnings
        assert lims_id_found_in_warnings


def test_fetch_capture_kit_from_status_db(report_api):

    # GIVEN an initialised report_api and the db returns samples with capture kit

    # WHEN fetching status data
    samples = report_api._fetch_family_samples_from_status_db(family_id="yellowhog")

    # THEN the report data should have capture kit
    assert samples
    for sample in samples:
        assert sample.get("capture_kit") == "GMSmyeloid"


def test_data_analysis_kit_from_status_db(report_api):

    # GIVEN an initialised report_api and the db returns samples with data_analysis

    # WHEN fetching status data
    samples = report_api._fetch_family_samples_from_status_db(family_id="yellowhog")

    # THEN the report data should have capture kit
    assert samples
    for sample in samples:
        assert sample.get("data_analysis") == "PIM"


def test_get_application_data_from_status_db(report_samples, report_api):
    # GIVEN data from an analysed case and an initialised report_api

    # WHEN fetch_application_data_from_status_db
    samples = report_samples
    application_data = report_api._get_application_data_from_status_db(samples)

    # THEN
    # the generated data has a property apptags with a value
    assert application_data["applications"]


def test_get_application_data_from_status_db_all_accredited(report_samples, report_api):
    # GIVEN data from an analysed case and an initialised report_api
    report_api.store._application_accreditation = True

    # WHEN fetch_application_data_from_status_db
    samples = report_samples
    application_data = report_api._get_application_data_from_status_db(samples)

    # THEN the generated data has a property accredited with a value
    assert application_data["accredited"] is True


def test_get_application_data_from_status_db_none_accredited(report_samples, report_api):
    # GIVEN data from an analysed case and an initialised report_api
    report_api.store._application_accreditation = False

    # WHEN fetch_application_data_from_status_db
    samples = report_samples
    application_data = report_api._get_application_data_from_status_db(samples)

    # THEN the generated data has a property accredited with a value
    assert application_data["accredited"] is False

import datetime
import os
from pathlib import Path

from cg.meta.report.api import ReportAPI


def test_collect_delivery_data(report_api, report_store, case_id):
    # GIVEN an initialised report_api and a case ready for delivery report creation

    # WHEN collecting delivery data for a certain case
    case = report_store.family(case_id)
    assert case
    assert case.links
    assert case.analyses
    delivery_data = report_api._get_delivery_data(case_id=case_id)

    # THEN all data for the delivery report should have been collected
    assert delivery_data["report_version"]
    assert delivery_data["previous_report_version"]
    assert delivery_data["case"]
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
        assert sample["delivered_at"]

        assert sample["million_read_pairs"]
        assert sample["mapped_reads"]
        assert sample["target_coverage"]
        assert sample["target_completeness"]
        assert sample["duplicates"]
        assert sample["processing_time"]
        assert sample["analysis_sex"]

    assert delivery_data["pipeline"]
    assert delivery_data["pipeline_version"]
    assert delivery_data["genome_build"]


def is_similar_dicts(dict1, dict2):
    _is_similar = True

    for key in dict1.keys():
        _is_similar = _is_similar and is_similar_values(dict1.get(key), dict2.get(key))

    return _is_similar


def is_similar_lists(list1, list2):
    _is_similar = True

    if isinstance(list2, list):
        for value1, value2 in zip(list1, list2):
            _is_similar = _is_similar and is_similar_values(value1, value2)
    else:
        for value1 in list1:
            _is_similar = _is_similar and value1 in list2

    return _is_similar


def is_similar_values(value1, value2):

    if str(value1) == str(value2):
        return True

    if isinstance(value1, dict):
        return is_similar_dicts(value1, value2)

    if isinstance(value1, list):
        return is_similar_lists(value1, value2)

    if isinstance(value1, datetime.datetime):
        return str(value1.date()) == value2

    if is_float(value1):
        return round(float(value1), 1) == round(float(value2), 1)

    return False


def is_float(value):
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def test_presentable_delivery_report_contains_delivery_data(report_api, case_id):
    # GIVEN data from an analysed case and an initialised report_api
    delivery_data = report_api._get_delivery_data(case_id=case_id)

    # WHEN creating delivery report
    presentable_data = report_api._make_data_presentable(delivery_data)

    # THEN
    # the delivery_report contains the delivery_data
    assert is_similar_dicts(delivery_data, presentable_data)


def dict_values_exists_in(a_dict: dict, a_target: str):

    all_exists = True

    for value in a_dict.values():
        all_exists = all_exists and value_exists_in(value, a_target)
    return all_exists


def value_exists_in(value, a_target: str):

    if isinstance(value, str):
        return value in a_target
    if isinstance(value, float):
        return str(round(value, 2)) in a_target or str(round(value, 1)) in a_target
    if isinstance(value, dict):
        return dict_values_exists_in(value, a_target)
    if isinstance(value, list):
        return list_values_exists_in(value, a_target)
    if isinstance(value, datetime.datetime):
        return str(value.date()) in a_target

    if str(value) in a_target:
        return True

    if isinstance(value, bool):
        return True

    return False


def list_values_exists_in(a_list: list, a_target: str):

    all_exists = True

    for value in a_list:
        all_exists = all_exists and value_exists_in(value, a_target)
    return all_exists


def test_create_delivery_report_contains_delivery_data(report_api):
    # GIVEN data from an analysed case and an initialised report_api
    case_id = "yellowhog"
    delivery_data = report_api._get_delivery_data(case_id=case_id)

    # WHEN creating delivery report
    delivery_report = report_api.create_delivery_report(case_id)

    # THEN
    # the delivery_report contains the delivery_data
    assert dict_values_exists_in(delivery_data, delivery_report)


def test_get_status_from_status_db(report_api):
    # GIVEN data from an analysed case and an initialised report_api

    # WHEN fetch_application_data_from_status_db
    samples = report_api._fetch_case_samples_from_status_db("yellowhog")

    # THEN the samples contain a status
    for sample in samples:
        assert sample["status"]


def test_incorporate_lims_methods(report_samples, report_api):
    # GIVEN data from an analysed case and an initialised report_api

    # WHEN fetch_and_add_lims_methods
    samples = report_samples
    report_api._incorporate_lims_methods(samples)

    # THEN
    # each sample has a property library_prep_method with a value
    for sample in samples:
        assert sample["prep_method"]

    # each sample has a property sequencing_method with a value
    for sample in samples:
        assert sample["sequencing_method"]


def test_render_delivery_report(report_api):
    # GIVEN proper qc data from an analysis exist
    delivery_data = report_api._get_delivery_data(case_id="yellowhog")
    report_data = report_api._make_data_presentable(delivery_data)

    # WHEN rendering a report from that data
    rendered_report = ReportAPI._render_delivery_report(report_data)

    # THEN a html report with certain data should have been rendered
    assert len(rendered_report) > 0


def test_create_delivery_report(report_api):
    # GIVEN initialized ReportAPI

    # WHEN rendering a report from that data
    created_report = report_api.create_delivery_report(case_id="yellowhog")

    # THEN a html report with certain data should have been rendered
    assert len(created_report) > 0


def test_create_delivery_report_file(report_api: ReportAPI):
    # GIVEN initialized ReportAPI

    # WHEN rendering a report from that data
    created_report_file = report_api.create_delivery_report_file(
        case_id="yellowhog", file_path=Path(".")
    )

    # THEN a html report with certain data should have been created on disk
    assert os.path.isfile(created_report_file.name)
    os.unlink(created_report_file.name)


def test_incorporate_coverage_data(report_api, report_samples):
    # GIVEN an initialised report_api and the chanjo_api does not return what we want
    report_api.chanjo._sample_coverage_returns_none = True
    samples = report_samples

    # WHEN failing to get latest trending data for a case
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
    samples = report_api._fetch_case_samples_from_status_db(case_id="yellowhog")

    # THEN the report data should have capture kit
    assert samples
    for sample in samples:
        assert sample.get("capture_kit") == "GMSmyeloid"


def test_data_analysis_kit_from_status_db(report_api, case_id):
    # GIVEN an initialised report_api and the db returns samples with data_analysis

    # WHEN fetching status data
    samples = report_api._fetch_case_samples_from_status_db(case_id=case_id)

    # THEN the report data should have capture kit
    assert samples
    for sample in samples:
        assert sample.get("capture_kit")


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


def test_render_accredited_delivery_report(report_api):
    # GIVEN proper qc data from an analysis exist with accredited application
    report_api.store._application_accreditation = True
    delivery_data = report_api._get_delivery_data(case_id="yellowhog")
    report_data = report_api._make_data_presentable(delivery_data)
    assert report_data["accredited"] is True

    # WHEN rendering a report from that data
    rendered_report = ReportAPI._render_delivery_report(report_data)

    # THEN a html report with swedac logo should have been rendered
    assert "SWEDAC logo" in rendered_report


def test_render_non_accredited_delivery_report(report_api):
    # GIVEN proper qc data from an analysis exist with non accredited application
    report_api.store._application_accreditation = False
    delivery_data = report_api._get_delivery_data(case_id="yellowhog")
    report_data = report_api._make_data_presentable(delivery_data)
    assert report_data["accredited"] is False

    # WHEN rendering a report from that data
    rendered_report = ReportAPI._render_delivery_report(report_data)

    # THEN a html report without swedac logo should have been rendered
    assert "SWEDAC logo" not in rendered_report


def test_get_delivery_data_not_accredited(report_api, report_store, case_id):
    # GIVEN an initialised report_api and a case ready for delivery report creation
    # GIVEN the case has samples that have at least one non accredited application

    # WHEN collecting delivery data for case
    case = report_store.family(case_id)
    assert case.links
    for link in case.links:
        link.sample.application_version.application.is_accredited = False

    delivery_data = report_api._get_delivery_data(case_id=case_id)

    # THEN the accreditation status int the delivery_data is false
    assert delivery_data["accredited"] is False


def test_get_delivery_data_accredited(report_api, report_store, case_id):
    # GIVEN an initialised report_api and a case ready for delivery report creation
    # GIVEN the case has samples that all have accredited application

    # WHEN collecting delivery data for case
    case = report_store.family(case_id)
    for link in case.links:
        link.sample.application_version.application.is_accredited = True
    delivery_data = report_api._get_delivery_data(case_id=case_id)

    # THEN the accreditation status int the delivery_data is true
    assert delivery_data["accredited"] is True

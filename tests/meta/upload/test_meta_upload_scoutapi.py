

def test_add_delivery_report_to_case_without_report(upload_scout_api):

    # GIVEN an existing case without delivery report
    customer_id = 'cust000'
    family_id = 'angrybird'
    report_path = '/delivery_report'

    # WHEN adding a delivery report to that case
    upload_scout_api.add_delivery_report(institute_id=customer_id, display_name=family_id,
                                         report_path=report_path)

    # THEN the delivery report should be retrievable for that case
    existing_case = upload_scout_api.scout.case(institute_id=customer_id, display_name=family_id)
    assert existing_case.delivery_report == report_path


def test_add_delivery_report_to_case_with_report(upload_scout_api):

    # GIVEN an existing case with a delivery report
    customer_id = 'cust000'
    family_id = 'angrybird'
    report_path_first = '/delivery_report'
    upload_scout_api.add_delivery_report(institute_id=customer_id, display_name=family_id,
                                         report_path=report_path_first)
    report_path_second = '/delivery_report2'

    # WHEN adding a delivery report to that case
    upload_scout_api.add_delivery_report(institute_id=customer_id, display_name=family_id,
                                         report_path=report_path_second)

    # THEN the latest delivery report should be retrievable that case
    existing_case = upload_scout_api.scout.case(institute_id=customer_id, display_name=family_id)
    assert existing_case.delivery_report == report_path_second

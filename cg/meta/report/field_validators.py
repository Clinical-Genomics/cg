# Report field validation helper

from cg.models.report.report import ReportModel


def get_missing_report_data(report_data: ReportModel, required_fields: dict):
    """Retrieve empty and missing fields from a specific report model"""

    missing_fields = dict()
    empty_fields = dict()

    def update_missing_data_dict(dict: dict, source: str, field: str, id: str):
        """Populates a dictionary with the missing/empty fields"""

        if source in dict.keys():
            if id:
                # If it's a sample/application dependant field, the ID/TAG is stored to uniquely identify it
                try:
                    dict[source][id].append(field)
                except KeyError:
                    dict[source][id] = field
                except AttributeError:
                    dict[source][id] = [dict[source][id], field]
            else:
                try:
                    dict[source].append(field)
                except AttributeError:
                    dict[source] = [dict[source], field]
        else:
            dict.update({source: {id: field} if id else field})

    def update_missing_data(data: dict, source: str, id: str = None):
        """Updates the missing or empty fields from an input report data"""

        for field, value in data.items():
            if not value or value == "N/A":
                update_missing_data_dict(empty_fields, source, field, id)
                if field in required_fields[source]:
                    update_missing_data_dict(missing_fields, source, field, id)

    update_missing_data(report_data.dict(), "report")
    update_missing_data(report_data.customer.dict(), "customer")
    update_missing_data(report_data.case.dict(), "case")
    for application in report_data.case.applications:
        update_missing_data(application.dict(), "applications", application.tag)
    update_missing_data(report_data.case.data_analysis.dict(), "data_analysis")
    for sample in report_data.case.samples:
        update_missing_data(sample.dict(), "samples", sample.id)
        update_missing_data(sample.methods.dict(), "methods", sample.id)
        update_missing_data(sample.timestamp.dict(), "timestamp", sample.id)
        update_missing_data(sample.metadata.dict(), "metadata", sample.id)

    return missing_fields, empty_fields

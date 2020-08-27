import datetime as dt
from itertools import groupby
from sqlalchemy import func

from cg.store import models
from cg.store.api.base import BaseHandler

MONTHS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


class TrendsHandler(BaseHandler):
    """Deprecated in favour of Vogue"""

    @staticmethod
    def get_last_day_of_previous_year(year: int):
        return TrendsHandler.get_last_day_of_year(year - 1)

    @staticmethod
    def get_last_day_of_year(year):
        return dt.date(year, 12, 31)

    @staticmethod
    def get_from_date(year):
        return TrendsHandler.get_last_day_of_previous_year(int(year))

    @staticmethod
    def get_until_date(year):
        return TrendsHandler.get_last_day_of_year(int(year))

    def samples_per_month(self, year):
        """Fetch samples per month. Grouped by priority."""
        query = (
            self.session.query(
                models.Customer.priority.label("priority"),
                func.month(models.Sample.received_at).label("month_no"),
                func.count(models.Sample.id).label("count"),
            )
            .join(models.Sample.customer)
            .filter(
                models.Sample.received_at > self.get_from_date(year),
                models.Sample.received_at < self.get_until_date(year),
            )
            .group_by("priority", "month_no")
        )

        for cust_priority, results in groupby(query, key=lambda result: result.priority):
            counts = {MONTHS[result.month_no]: result.count for result in results}
            data = {
                "name": cust_priority,
                "results": {month: counts.get(month) or None for month in MONTHS.values()},
            }
            yield data

    def samples_per_month_application(self, year):
        """Fetch samples per month. Grouped by application cathegory."""

        query = (
            self.session.query(
                models.Application.category.label("category"),
                func.month(models.Sample.received_at).label("month_no"),
                func.count(models.Sample.id).label("count"),
            )
            .join(
                models.Sample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.Sample.received_at > self.get_from_date(year),
                models.Sample.received_at < self.get_until_date(year),
                models.Sample.received_at,
                models.Application.category,
            )
            .group_by("category", "month_no")
        )

        for application_cathegory, results in groupby(query, key=lambda result: result.category):
            counts = {MONTHS[result.month_no]: result.count for result in results}
            data = {
                "name": application_cathegory,
                "results": {month: counts.get(month) or None for month in MONTHS.values()},
            }
            yield data

    def received_to_delivered(self, year):
        """Calculate averages from received to delivered."""
        query = (
            self.session.query(
                models.Application.category.label("category"),
                func.month(models.Sample.received_at).label("month_no"),
                (
                    func.avg(
                        func.datediff(models.Sample.delivered_at, models.Sample.received_at)
                    ).label("average")
                ),
            )
            .join(
                models.Sample.customer,
                models.Sample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.Customer.priority == "diagnostic",
                models.Sample.received_at > self.get_from_date(year),
                models.Sample.received_at < self.get_until_date(year),
                models.Sample.delivered_at is not None,
            )
            .group_by(
                models.Application.category,
                func.month(models.Sample.received_at),
            )
        )
        for category, results in groupby(query, key=lambda result: result.category):
            averages = {
                MONTHS[result.month_no]: float(result.average) if result.average else None
                for result in results
            }
            yield {
                "name": category,
                "results": {month: averages.get(month) or None for month in MONTHS.values()},
            }

    def received_to_prepped(self, year):
        """Calculate averages to prepp samples."""
        query = (
            self.session.query(
                models.Application.category.label("category"),
                func.month(models.Sample.received_at).label("month_no"),
                (
                    func.avg(
                        func.datediff(models.Sample.prepared_at, models.Sample.received_at)
                    ).label("average")
                ),
            )
            .join(
                models.Sample.customer,
                models.Sample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.Customer.priority == "diagnostic",
                models.Sample.received_at > self.get_from_date(year),
                models.Sample.received_at < self.get_until_date(year),
            )
            .group_by(
                models.Application.category,
                func.month(models.Sample.received_at),
            )
        )
        for category, results in groupby(query, key=lambda result: result.category):
            averages = {
                MONTHS[result.month_no]: float(result.average) if result.average else None
                for result in results
            }
            yield {
                "name": category,
                "results": {month: averages.get(month) or None for month in MONTHS.values()},
            }

    def prepped_to_sequenced(self, year):
        """Calculate average to sequence samples."""
        query = (
            self.session.query(
                models.Application.category.label("category"),
                func.month(models.Sample.received_at).label("month_no"),
                func.avg(
                    func.datediff(models.Sample.sequenced_at, models.Sample.prepared_at)
                ).label("average"),
            )
            .join(
                models.Sample.customer,
                models.Sample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.Customer.priority == "diagnostic",
                models.Sample.received_at > self.get_from_date(year),
                models.Sample.received_at < self.get_until_date(year),
            )
            .group_by(
                models.Application.category,
                func.month(models.Sample.received_at),
            )
        )
        for category, results in groupby(query, key=lambda result: result.category):
            averages = {
                MONTHS[result.month_no]: float(result.average) if result.average else None
                for result in results
            }
            yield {
                "name": category,
                "results": {month: averages.get(month) or None for month in MONTHS.values()},
            }

    def sequenced_to_delivered(self, year):
        """Calculate average to deliver samples."""
        query = (
            self.session.query(
                models.Application.category.label("category"),
                func.month(models.Sample.received_at).label("month_no"),
                func.avg(
                    func.datediff(models.Sample.delivered_at, models.Sample.sequenced_at)
                ).label("average"),
            )
            .join(
                models.Sample.customer,
                models.Sample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.Customer.priority == "diagnostic",
                models.Sample.received_at > self.get_from_date(year),
                models.Sample.received_at < self.get_until_date(year),
                models.Sample.delivered_at is not None,
            )
            .group_by(
                models.Application.category,
                func.month(models.Sample.received_at),
            )
        )
        for category, results in groupby(query, key=lambda result: result.category):
            averages = {
                MONTHS[result.month_no]: float(result.average) if result.average else None
                for result in results
            }
            yield {
                "name": category,
                "results": {month: averages.get(month) or None for month in MONTHS.values()},
            }

    def delivered_to_invoiced(self, year):
        """Calculate average time to invoice samples."""
        query = (
            self.session.query(
                models.Application.category.label("category"),
                func.month(models.Sample.received_at).label("month_no"),
                func.avg(
                    func.datediff(models.Invoice.invoiced_at, models.Sample.delivered_at)
                ).label("average"),
            )
            .join(
                models.Sample.customer,
                models.Sample.application_version,
                models.ApplicationVersion.application,
                models.Sample.invoice,
            )
            .filter(
                models.Customer.priority == "diagnostic",
                models.Sample.received_at > self.get_from_date(year),
                models.Sample.received_at < self.get_until_date(year),
                models.Sample.delivered_at is not None,
                models.Sample.invoice is not None,
                models.Sample.invoice_id is not None,
                models.Invoice.invoiced_at is not None,
            )
            .group_by(
                models.Application.category,
                func.month(models.Sample.received_at),
            )
        )
        for category, results in groupby(query, key=lambda result: result.category):
            averages = {
                MONTHS[result.month_no]: float(result.average) if result.average else None
                for result in results
            }
            yield {
                "name": category,
                "results": {month: averages.get(month) or None for month in MONTHS.values()},
            }

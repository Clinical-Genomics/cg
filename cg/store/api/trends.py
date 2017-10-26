import datetime as dt
from itertools import groupby

from sqlalchemy import func, text

from cg.store import models

MONTHS = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
          7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}


class TrendsHandler:

    def samples_per_month(self):
        """Fetch samples per month."""
        query = (
            self.session.query(
                models.Customer.priority.label('priority'),
                func.month(models.Sample.received_at).label('month_no'),
                func.count(models.Sample.id).label('count'),
            )
            .join(models.Sample.customer)
            .filter(models.Sample.received_at > dt.datetime(2016, 12, 31))
            .group_by(models.Customer.priority, func.month(models.Sample.received_at))
        )
        for cust_priority, results in groupby(query, key=lambda result: result.priority):
            counts = {MONTHS[result.month_no]: result.count for result in results}
            data = {
                'name': cust_priority,
                'results': [{
                    'month': month,
                    'count': counts.get(month) or None,
                } for month in MONTHS.values()],
            }
            yield data

    def received_to_delivered(self):
        """Calculate averages from received to delivered."""
        query = (
            self.session.query(
                models.Application.category.label('category'),
                func.month(models.Sample.received_at).label('month_no'),
                (func.avg(func.datediff(models.Sample.delivered_at, models.Sample.received_at))
                     .label('average')),
            )
            .join(
                models.Sample.customer,
                models.Sample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.Customer.priority == 'diagnostic',
                models.Sample.received_at > dt.datetime(2016, 12, 31),
                models.Sample.delivered_at != None,
            )
            .group_by(func.month(models.Sample.received_at))
        )
        for category, results in groupby(query, key=lambda result: result.category):
            averages = {MONTHS[result.month_no]: float(result.average) for result in results}
            yield {
                'category': category,
                'results': [{
                    'month': month,
                    'average': averages.get(month) or None,
                } for month in MONTHS.values()]
            }

    def received_to_prepped(self):
        """Calculate averages to prepp samples."""
        query = (
            self.session.query(
                models.Application.category.label('category'),
                func.month(models.Sample.received_at).label('month_no'),
                (func.avg(func.datediff(models.Sample.prepared_at, models.Sample.received_at))
                     .label('average')),
            )
            .join(
                models.Sample.customer,
                models.Sample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.Customer.priority == 'diagnostic',
                models.Sample.received_at > dt.datetime(2016, 12, 31)
            )
            .group_by(func.month(models.Sample.received_at))
        )
        for category, results in groupby(query, key=lambda result: result.category):
            averages = {MONTHS[result.month_no]: float(result.average) for result in results}
            yield {
                'category': category,
                'results': [{
                    'month': month,
                    'average': averages.get(month) or None,
                } for month in MONTHS.values()]
            }

    def prepped_to_sequenced(self):
        """Calculate average to sequence samples."""
        query = (
            self.session.query(
                models.Application.category.label('category'),
                func.month(models.Sample.received_at).label('month_no'),
                func.avg(func.datediff(models.Sample.sequenced_at, models.Sample.prepared_at)).label('average'),
            )
            .join(
                models.Sample.customer,
                models.Sample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.Customer.priority == 'diagnostic',
                models.Sample.received_at > dt.datetime(2016, 12, 31)
            )
            .group_by(func.month(models.Sample.received_at))
        )
        for category, results in groupby(query, key=lambda result: result.category):
            averages = {MONTHS[result.month_no]: float(result.average) for result in results}
            yield {
                'category': category,
                'results': [{
                    'month': month,
                    'average': averages.get(month) or None,
                } for month in MONTHS.values()]
            }
    
    def sequenced_to_delivered(self):
        """Calculate average to deliver samples."""
        query = (
            self.session.query(
                models.Application.category.label('category'),
                func.month(models.Sample.received_at).label('month_no'),
                func.avg(func.datediff(models.Sample.delivered_at, models.Sample.sequenced_at)).label('average'),
            )
            .join(
                models.Sample.customer,
                models.Sample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.Customer.priority == 'diagnostic',
                models.Sample.received_at > dt.datetime(2016, 12, 31),
                models.Sample.delivered_at != None,
            )
            .group_by(func.month(models.Sample.received_at))
        )
        for category, results in groupby(query, key=lambda result: result.category):
            averages = {MONTHS[result.month_no]: float(result.average) for result in results}
            yield {
                'category': category,
                'results': [{
                    'month': month,
                    'average': averages.get(month) or None,
                } for month in MONTHS.values()]
            }

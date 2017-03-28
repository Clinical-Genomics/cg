# -*- coding: utf-8 -*-
from sqlservice import SQLClient

from .models import Model, Case


class QueueApi(object):

    """docstring for QueueApi"""

    def __init__(self, db_uri):
        super(QueueApi, self).__init__()
        self.db_uri = db_uri
        self.db = None
        self.connect()

    def connect(self):
        """Connect to the database."""
        self.db = SQLClient({'SQL_DATABASE_URI': self.db_uri}, model_class=Model)

    def case(self, case_id):
        """Fetch a case from the database."""
        return self.db.Case.get(case_id)

    def case_by_name(self, case_name):
        """Fetch a case by name."""
        return self.db.Case.filter_by(case_id=case_name).first()

    def save_case(self, case_data):
        """Save a new case to the database."""
        return self.db.Case.save(case_data)

    def cases(self, lims_ok=None):
        """Return cases in order of highest priority."""
        query = self.db.Case.order_by(Case.is_prioritized.desc(),
                                      Case.last_analyzed_at.desc())
        if lims_ok is not None:
            query = query.filter_by(lims_ok=lims_ok)
        return query

    def flowcell(self, flowcell_id, sample_id):
        """Return result for a flowcell and sample."""
        return self.db.Flowcell.filter_by(flowcell_id=flowcell_id, sample_id=sample_id).first()

    def save_flowcell(self, flowcell_data):
        """Save a new flowcell (+ sample) entry to the database."""
        return self.db.Flowcell.save(flowcell_data)

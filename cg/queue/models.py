# -*- coding: utf-8 -*-
from sqlalchemy import Column, types, orm, ForeignKey, UniqueConstraint
from sqlservice import declarative_base

Model = declarative_base()


class Case(Model):

    __tablename__ = 'case'

    id = Column(types.Integer, primary_key=True)
    case_id = Column(types.String(256))
    last_analyzed_at = Column(types.DateTime())
    is_prioritized = Column(types.Boolean)
    lims_ok = Column(types.Boolean)
    lims_error = Column(types.Text)

    flowcells = orm.relationship('Flowcell', cascade='all,delete', backref='case')

    def is_ready(self):
        """Check if the case is ready for analysis."""
        linked_fcs = len(self.flowcells) > 0
        flowcells_ok = all(flowcell_obj.has_fastqs for flowcell_obj in self.flowcells)
        return self.lims_ok and linked_fcs and flowcells_ok


class Flowcell(Model):

    __tablename__ = 'flowcell'
    __table_args__ = (
        UniqueConstraint('flowcell_id', 'sample_id', name='_flowcell_sample_uc'),
    )

    id = Column(types.Integer, primary_key=True)
    flowcell_id = Column(types.String(128))
    sample_id = Column(types.String(128))
    case_id = Column(ForeignKey(Case.id))
    is_fetched = Column(types.Boolean, default=False)
    has_fastqs = Column(types.Boolean, default=False)

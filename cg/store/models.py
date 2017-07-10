# -*- coding: utf-8 -*-
import datetime as dt

import alchy
from sqlalchemy import Column, ForeignKey, orm, types, UniqueConstraint, Table

Model = alchy.make_declarative_base(Base=alchy.ModelBase)


class User(Model):

    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(128), nullable=False)
    email = Column(types.String(128), unique=True, nullable=False)
    is_admin = Column(types.Boolean, default=False)

    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)


class Customer(Model):

    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)

    families = orm.relationship('Family', backref='customer')
    samples = orm.relationship('Sample', backref='customer')
    users = orm.relationship('User', backref='customer')


class FamilySample(Model):

    __table_args__ = (
        UniqueConstraint('family_id', 'sample_id', name='_family_sample_uc'),
    )

    id = Column(types.Integer, primary_key=True)
    family_id = Column(ForeignKey('family.id', ondelete='CASCADE'), nullable=False)
    sample_id = Column(ForeignKey('sample.id', ondelete='CASCADE'), nullable=False)
    status = Column(types.Enum('affected', 'unaffected', 'unknown'), nullable=False)
    mother_id = Column(ForeignKey('sample_id'))
    father_id = Column(ForeignKey('sample_id'))

    mother = orm.relationship('Sample', foreign_keys=[mother_id])
    father = orm.relationship('Sample', foreign_keys=[father_id])
    family = orm.relationship('Sample', foreign_keys=[sample_id], backref='samples')


class Family(Model):

    __table_args__ = (
        UniqueConstraint('customer_id', 'name', name='_customer_name_uc'),
    )

    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)
    priority = Column(types.Integer, default=1, nullable=False)
    _panels = Column(types.Text, nullable=False)

    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)

    analyses = orm.relationship('Analysis', backref='family', order_by='-Analysis.analyzed_at')

    @property
    def panels(self):
        """Return a list of panels."""
        panel_list = self._panels.split(',') if self._panels else []
        return panel_list

    @panels.setter
    def panels(self, panel_list):
        self._panels = ','.join(panel_list) if panel_list else None


class Sample(Model):

    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), nullable=False, unique=True)
    name = Column(types.String(128), nullable=False)
    received_at = Column(types.DateTime)
    is_external = Column(types.Boolean, default=False)
    sequenced_at = Column(types.DateTime)
    sex = Column(types.Enum('male', 'female', 'unknown'), nullable=False)

    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)


flowcell_sample = Table(
    'flowcell_sample',
    Model.metadata,
    Column('flowcell_id', types.Integer, ForeignKey('flowcell.id'), nullable=False),
    Column('sample_id', types.Integer, ForeignKey('sample.id'), nullable=False),
    UniqueConstraint('flowcell_id', 'sample_id', name='_flowcell_sample_uc'),
)


class Flowcell(Model):

    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(32), unique=True, nullable=False)
    sequencer_type = Column(types.Enum('hiseqga', 'hiseqx'))
    sequencer_name = Column(types.String(32))
    sequenced_at = Column(types.DateTime)

    samples = orm.relationship('Sample', secondary=flowcell_sample, backref='flowcells')


class Analysis(Model):

    id = Column(types.Integer, primary_key=True)
    pipeline = Column(types.String(32), nullable=False)
    pipeline_version = Column(types.String(32))
    created_at = Column(types.DateTime, default=dt.datetime.now, nullable=False)
    analyzed_at = Column(types.DateTime)
    # primary analysis is the one originally delivered to the customer
    is_primary = Column(types.Boolean, default=False)

    family_id = Column(ForeignKey('family.id', ondelete='CASCADE'), nullable=False)

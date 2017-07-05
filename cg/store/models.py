# -*- coding: utf-8 -*-
import datetime as dt

import alchy
from sqlalchemy import Column, ForeignKey, orm, types, UniqueConstraint, Table

Model = alchy.make_declarative_base(Base=alchy.ModelBase)


class ModelBase(Model):
    id = Column(types.Integer, primary_key=True)


class User(ModelBase):

    __tablename__ = 'user'

    name = Column(types.String(128), nullable=False)
    email = Column(types.String(128), unique=True, nullable=False)
    is_admin = Column(types.Boolean, default=False)


class Customer(ModelBase):

    __tablename__ = 'customer'

    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)

    families = orm.relationship('Family', cascade='all,delete', backref='customer')
    samples = orm.relationship('Sample', cascade='all,delete', backref='customer')


family_sample = Table(
    'family_sample',
    Model.metadata,
    Column('family_id', types.Integer, ForeignKey('family.id'), nullable=False),
    Column('sample_id', types.Integer, ForeignKey('sample.id'), nullable=False),
    UniqueConstraint('family_id', 'sample_id', name='_family_sample_uc'),
)


class Family(ModelBase):

    __tablename__ = 'family'

    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)

    customer_id = Column(ForeignKey('customer.id'), nullable=False)

    samples = orm.relationship('Sample', secondary=family_sample, backref='families')
    analyses = orm.relationship('Analysis', cascade='all,delete', backref='family')


class Sample(ModelBase):

    __tablename__ = 'sample'

    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)
    received_at = Column(types.DateTime)
    priority = Column(types.Integer, default=0, nullable=False)
    is_external = Column(types.Boolean, default=False)
    sequenced_at = Column(types.DateTime)

    customer_id = Column(ForeignKey('customer.id'), nullable=False)


class FlowcellSample(ModelBase):

    __tablename__ = 'flowcell_sample'
    __table_args__ = (
        UniqueConstraint('flowcell_id', 'sample_id', name='_flowcell_sample_uc'),
    )

    reads = Column(types.Integer, nullable=False)
    flowcell_id = Column(ForeignKey('flowcell.id'), nullable=False)
    sample_id = Column(ForeignKey('sample.id'), nullable=False)


class Flowcell(ModelBase):

    __tablename__ = 'flowcell'

    name = Column(types.String(32), unique=True, nullable=False)
    sequencer_type = Column(types.Enum('hiseqga', 'hiseqx'))
    sequencer_name = Column(types.String(32))
    sequenced_at = Column(types.DateTime)

    samples = orm.relationship('Sample', secondary=FlowcellSample, backref='flowcells')


class Analysis(ModelBase):

    __tablename__ = 'analysis'

    pipeline = Column(types.String(32), nullable=False)
    pipeline_version = Column(types.String(32))
    created_at = Column(types.DateTime, default=dt.datetime.now, nullable=False)
    analyzed_at = Column(types.DateTime)
    # primary analysis is the one originally delivered to the customer
    is_primary = Column(types.Boolean, default=False)

    family_id = Column(ForeignKey('family.id'), nullable=False)

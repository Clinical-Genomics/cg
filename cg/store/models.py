# -*- coding: utf-8 -*-
import datetime as dt
from typing import List

import alchy
from sqlalchemy import Column, ForeignKey, orm, types, UniqueConstraint, Table

Model = alchy.make_declarative_base(Base=alchy.ModelBase)


class User(Model):

    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(128), nullable=False)
    email = Column(types.String(128), unique=True, nullable=False)
    is_admin = Column(types.Boolean, default=False)

    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    customer = orm.relationship('Customer', backref='users')

    def __str__(self) -> str:
        return self.name


class Customer(Model):

    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)
    priority = Column(types.Enum('diagnostic', 'research'))

    scout_access = Column(types.Boolean, default=False)
    agreement_date = Column(types.DateTime)
    agreement_registration = Column(types.String(32))
    project_account_ki = Column(types.String(32))
    project_account_kth = Column(types.String(32))
    organisation_number = Column(types.String(32))
    invoice_address = Column(types.Text)
    invoice_reference = Column(types.String(32))
    uppmax_account = Column(types.String(32))

    primary_contact = Column(types.String(128))
    delivery_contact = Column(types.String(128))
    invoice_contact = Column(types.String(128))

    families = orm.relationship('Family', backref='customer', order_by='-Family.id')
    samples = orm.relationship('Sample', backref='customer', order_by='-Sample.id')

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"


class FamilySample(Model):

    __table_args__ = (
        UniqueConstraint('family_id', 'sample_id', name='_family_sample_uc'),
    )

    id = Column(types.Integer, primary_key=True)
    family_id = Column(ForeignKey('family.id', ondelete='CASCADE'), nullable=False)
    sample_id = Column(ForeignKey('sample.id', ondelete='CASCADE'), nullable=False)
    status = Column(types.Enum('affected', 'unaffected', 'unknown'), nullable=False)
    mother_id = Column(ForeignKey('sample.id'))
    father_id = Column(ForeignKey('sample.id'))

    family = orm.relationship('Family', backref='links')
    sample = orm.relationship('Sample', foreign_keys=[sample_id], backref='links')
    mother = orm.relationship('Sample', foreign_keys=[mother_id])
    father = orm.relationship('Sample', foreign_keys=[father_id])

    def to_dict(self, samples: bool=False) -> dict:
        """Override dicify method."""
        data = super(FamilySample, self).to_dict()
        if samples:
            data['sample'] = self.sample.to_dict()
            data['mother'] = self.mother.to_dict() if self.mother else None
            data['father'] = self.father.to_dict() if self.father else None
        return data

    def __str__(self) -> str:
        return f"{self.family.internal_id} | {self.sample.internal_id}"


class Family(Model):

    __table_args__ = (
        UniqueConstraint('customer_id', 'name', name='_customer_name_uc'),
    )

    id = Column(types.Integer, primary_key=True)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)
    priority = Column(types.Integer, default=1, nullable=False)
    _panels = Column(types.Text, nullable=False)
    analyze = Column(types.Boolean, default=False)

    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)

    analyses = orm.relationship('Analysis', backref='family', order_by='-Analysis.analyzed_at')

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    def to_dict(self, links: bool=False) -> dict:
        """Override dicify method."""
        data = super(Family, self).to_dict()
        if links:
            data['links'] = [link_obj.to_dict(samples=True) for link_obj in self.links]
        return data

    @property
    def panels(self) -> List[str]:
        """Return a list of panels."""
        panel_list = self._panels.split(',') if self._panels else []
        return panel_list

    @panels.setter
    def panels(self, panel_list: List[str]):
        self._panels = ','.join(panel_list) if panel_list else None


class Sample(Model):

    __table_args__ = (
        UniqueConstraint('customer_id', 'name', name='_customer_name_uc'),
    )

    id = Column(types.Integer, primary_key=True)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    internal_id = Column(types.String(32), nullable=False, unique=True)
    name = Column(types.String(128), nullable=False)
    order = Column(types.String(64))
    received_at = Column(types.DateTime)
    sequenced_at = Column(types.DateTime)
    delivered_at = Column(types.DateTime)
    sex = Column(types.Enum('male', 'female', 'unknown'), nullable=False)
    reads = Column(types.Integer, default=0)

    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    application_version_id = Column(ForeignKey('application_version.id'))

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"


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

    def __str__(self):
        return self.name


class Analysis(Model):

    id = Column(types.Integer, primary_key=True)
    pipeline = Column(types.String(32), nullable=False)
    pipeline_version = Column(types.String(32))
    created_at = Column(types.DateTime, default=dt.datetime.now, nullable=False)
    analyzed_at = Column(types.DateTime)
    housekeeper_id = Column(types.Integer)
    uploaded_at = Column(types.DateTime)
    delivered_at = Column(types.DateTime)
    # primary analysis is the one originally delivered to the customer
    is_primary = Column(types.Boolean, default=False)

    family_id = Column(ForeignKey('family.id', ondelete='CASCADE'), nullable=False)

    def __str__(self):
        return f"{self.family.internal_id} | {self.analyzed_at.date()}"


class Application(Model):

    id = Column(types.Integer, primary_key=True)
    tag = Column(types.String(32), unique=True, nullable=False)
    category = Column(types.Enum('wgs', 'wes', 'tga', 'rna', 'mic'), nullable=False)
    description = Column(types.String(256), nullable=False)

    is_accredited = Column(types.Boolean, nullable=False)
    turnaround_time = Column(types.Integer)
    minimum_order = Column(types.Integer, default=1)
    sequencing_depth = Column(types.Integer)
    target_reads = Column(types.BigInteger, default=0)
    sample_amount = Column(types.Integer)
    sample_volume = Column(types.Text)
    sample_concentration = Column(types.Text)
    priority_processing = Column(types.Boolean, default=False)
    details = Column(types.Text)
    limitations = Column(types.Text)
    percent_kth = Column(types.Integer)

    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)
    comment = Column(types.Text)

    versions = orm.relationship('ApplicationVersion', order_by='ApplicationVersion.version',
                                backref='application')

    def __str__(self) -> str:
        return self.tag

    @property
    def expected_reads(self):
        return self.target_reads * 0.75


class ApplicationVersion(Model):

    __table_args__ = (UniqueConstraint('application_id', 'version', name='_app_version_uc'),)

    id = Column(types.Integer, primary_key=True)
    version = Column(types.Integer, nullable=False)

    application_id = Column(ForeignKey(Application.id), nullable=False)
    valid_from = Column(types.DateTime, default=dt.datetime.now, nullable=False)
    price_standard = Column(types.Integer)
    price_priority = Column(types.Integer)
    price_express = Column(types.Integer)
    price_research = Column(types.Integer)

    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)
    comment = Column(types.Text)

    samples = orm.relationship('Sample', backref='application_version')

    def __str__(self) -> str:
        return f"{self.application.tag} ({self.version})"


class Panel(Model):

    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(64), unique=True)
    abbrev = Column(types.String(32), unique=True)
    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    current_version = Column(types.Float, nullable=False)
    date = Column(types.DateTime, nullable=False)
    gene_count = Column(types.Integer)

    customer = orm.relationship(Customer, backref='panels')

    def __str__(self):
        return f"{self.abbrev} ({self.current_version})"

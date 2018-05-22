# -*- coding: utf-8 -*-
import datetime as dt
from typing import List

import alchy
from sqlalchemy import Column, ForeignKey, orm, types, UniqueConstraint, Table

from cg import constants

Model = alchy.make_declarative_base(Base=alchy.ModelBase)


class PriorityMixin:

    @property
    def priority_human(self):
        """Humanized priority for sample."""
        return constants.REV_PRIORITY_MAP[self.priority]

    @priority_human.setter
    def priority_human(self, priority_str: str):
        self.priority = constants.PRIORITY_MAP.get(priority_str)

    @property
    def high_priority(self):
        """Has high priority?"""
        return self.priority > 1

    @property
    def low_priority(self):
        """Has low priority?"""
        return self.priority < 1


class User(Model):

    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(128), nullable=False)
    email = Column(types.String(128), unique=True, nullable=False)
    is_admin = Column(types.Boolean, default=False)

    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    customer = orm.relationship('Customer', backref='users')

    def to_dict(self) -> dict:
        """Override dicify method."""
        data = super(User, self).to_dict()
        data['customer'] = self.customer.to_dict()
        return data

    def __str__(self) -> str:
        return self.name


class Customer(Model):

    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)
    priority = Column(types.Enum('diagnostic', 'research'))
    scout_access = Column(types.Boolean, nullable=False, default=False)

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
    pools = orm.relationship('Pool', backref='customer', order_by='-Pool.id')

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

    def to_dict(self, parents: bool=False, samples: bool=False, family: bool=False) -> dict:
        """Override dicify method."""
        data = super(FamilySample, self).to_dict()
        if samples:
            data['sample'] = self.sample.to_dict()
            data['mother'] = self.mother.to_dict() if self.mother else None
            data['father'] = self.father.to_dict() if self.father else None
        elif parents:
            data['mother'] = self.mother.to_dict() if self.mother else None
            data['father'] = self.father.to_dict() if self.father else None
        if family:
            data['family'] = self.family.to_dict()
        return data

    def __str__(self) -> str:
        return f"{self.family.internal_id} | {self.sample.internal_id}"


class Family(Model, PriorityMixin):

    __table_args__ = (
        UniqueConstraint('customer_id', 'name', name='_customer_name_uc'),
    )

    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)
    priority = Column(types.Integer, default=1, nullable=False)
    _panels = Column(types.Text, nullable=False)
    action = Column(types.Enum(*constants.FAMILY_ACTIONS))
    comment = Column(types.Text)

    ordered_at = Column(types.DateTime, default=dt.datetime.now)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    analyses = orm.relationship('Analysis', backref='family', order_by='-Analysis.completed_at')

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    def to_dict(self, links: bool=False, analyses: bool=False) -> dict:
        """Override dicify method."""
        data = super(Family, self).to_dict()
        data['panels'] = self.panels
        data['priority'] = self.priority_human
        data['customer'] = self.customer.to_dict()
        if links:
            data['links'] = [link_obj.to_dict(samples=True) for link_obj in self.links]
        if analyses:
            data['analyses'] = [analysis_obj.to_dict(family=False) for analysis_obj in
                                self.analyses]
        return data

    @property
    def panels(self) -> List[str]:
        """Return a list of panels."""
        panel_list = self._panels.split(',') if self._panels else []
        return panel_list

    @panels.setter
    def panels(self, panel_list: List[str]):
        self._panels = ','.join(panel_list) if panel_list else None


class Delivery(Model):

    id = Column(types.Integer, primary_key=True)
    delivered_at = Column(types.DateTime)
    removed_at = Column(types.DateTime)
    destination = Column(types.Enum('caesar', 'pdc', 'uppmax', 'mh', 'custom'), default='caesar')
    sample_id = Column(ForeignKey('sample.id', ondelete='CASCADE'))
    pool_id = Column(ForeignKey('pool.id', ondelete='CASCADE'))
    comment = Column(types.Text)


class Pool(Model):

    __table_args__ = (UniqueConstraint('order', 'name', name='_order_name_uc'),)

    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(32), nullable=False)
    order = Column(types.String(64), nullable=False)
    ticket_number = Column(types.Integer)
    reads = Column(types.BigInteger, default=0)
    ordered_at = Column(types.DateTime, nullable=False)
    received_at = Column(types.DateTime)
    sequenced_at = Column(types.DateTime)
    delivered_at = Column(types.DateTime)
    invoice_id = Column(ForeignKey('invoice.id'))
    invoiced_at = Column(types.DateTime)  # DEPRECATED
    comment = Column(types.Text)
    lims_project = Column(types.Text)

    created_at = Column(types.DateTime, default=dt.datetime.now)
    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    application_version_id = Column(ForeignKey('application_version.id'), nullable=False)

    deliveries = orm.relationship('Delivery', backref='pool')


class Sample(Model, PriorityMixin):

    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), nullable=False, unique=True)
    priority = Column(types.Integer, default=1, nullable=False)
    name = Column(types.String(128), nullable=False)
    order = Column(types.String(64))
    ticket_number = Column(types.Integer)
    sex = Column(types.Enum('male', 'female', 'unknown'), nullable=False)
    is_external = Column(types.Boolean, default=False)  # DEPRECATED
    downsampled_to = Column(types.BigInteger)
    is_tumour = Column(types.Boolean, default=False)
    loqusdb_id = Column(types.String(64))
    capture_kit = Column(types.String(64))
    reads = Column(types.BigInteger, default=0)
    ordered_at = Column(types.DateTime, nullable=False)
    received_at = Column(types.DateTime)
    prepared_at = Column(types.DateTime)
    sequence_start = Column(types.DateTime)
    sequenced_at = Column(types.DateTime)
    delivered_at = Column(types.DateTime)
    invoiced_at = Column(types.DateTime)  # DEPRECATED
    invoice_id = Column(ForeignKey('invoice.id'))
    no_invoice = Column(types.Boolean, default=False)
    comment = Column(types.Text)
    beaconized_at = Column(types.Text)

    created_at = Column(types.DateTime, default=dt.datetime.now)
    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    application_version_id = Column(ForeignKey('application_version.id'), nullable=False)

    deliveries = orm.relationship('Delivery', backref='sample')

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    @property
    def state(self) -> str:
        """Get the current sample state."""
        if self.delivered_at:
            return f"Delivered {self.delivered_at.date()}"
        elif self.sequenced_at:
            return f"Sequenced {self.sequenced_at.date()}"
        elif self.sequence_start:
            return f"Sequencing {self.sequence_start.date()}"
        elif self.received_at:
            return f"Received {self.received_at.date()}"
        else:
            return f"Ordered {self.ordered_at.date()}"

    def to_dict(self, links: bool=False, flowcells: bool=False) -> dict:
        """Override dicify method."""
        data = super(Sample, self).to_dict()
        data['priority'] = self.priority_human
        data['customer'] = self.customer.to_dict()
        data['application_version'] = self.application_version.to_dict()
        data['application'] = self.application_version.application.to_dict()
        if links:
            data['links'] = [link_obj.to_dict(family=True, parents=True) for link_obj in
                             self.links]
        if flowcells:
            data['flowcells'] = [flowcell_obj.to_dict() for flowcell_obj in self.flowcells]
        return data


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
    archived_at = Column(types.DateTime)
    status = Column(types.Enum(*constants.FLOWCELL_STATUS), default='ondisk')

    samples = orm.relationship('Sample', secondary=flowcell_sample, backref='flowcells')

    def __str__(self):
        return self.name

    def to_dict(self, samples: bool=False):
        """Override dictify method."""
        data = super(Flowcell, self).to_dict()
        if samples:
            data['samples'] = [sample.to_dict() for sample in self.samples]
        return data


class Analysis(Model):

    id = Column(types.Integer, primary_key=True)
    pipeline = Column(types.String(32), nullable=False)
    pipeline_version = Column(types.String(32))
    started_at = Column(types.DateTime)
    completed_at = Column(types.DateTime)
    uploaded_at = Column(types.DateTime)
    delivered_at = Column(types.DateTime)
    # primary analysis is the one originally delivered to the customer
    is_primary = Column(types.Boolean, default=False)
    housekeeper_id = Column(types.Integer)

    created_at = Column(types.DateTime, default=dt.datetime.now, nullable=False)
    family_id = Column(ForeignKey('family.id', ondelete='CASCADE'), nullable=False)

    def __str__(self):
        return f"{self.family.internal_id} | {self.completed_at.date()}"

    def to_dict(self, family: bool=True):
        """Override dicify method."""
        data = super(Analysis, self).to_dict()
        if family:
            data['family'] = self.family.to_dict()
        return data


class Application(Model):

    id = Column(types.Integer, primary_key=True)
    tag = Column(types.String(32), unique=True, nullable=False)
    # DEPRECATED, use prep_category instead
    category = Column(types.Enum('wgs', 'wes', 'tga', 'rna', 'mic', 'rml'))
    prep_category = Column(types.Enum(*constants.PREP_CATEGORIES), nullable=False)
    is_external = Column(types.Boolean, nullable=False, default=False)
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
    comment = Column(types.Text)
    is_archived = Column(types.Boolean, default=False)

    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)
    versions = orm.relationship('ApplicationVersion', order_by='ApplicationVersion.version',
                                backref='application')

    def __str__(self) -> str:
        return self.tag

    @property
    def reduced_price(self):
        return self.tag.startswith('WGT') or self.tag.startswith('EXT')

    @property
    def expected_reads(self):
        return self.target_reads * 0.75

    @property
    def analysis_type(self):
        return 'wgs' if self.prep_category == 'wgs' else 'wes'


class ApplicationVersion(Model):

    __table_args__ = (UniqueConstraint('application_id', 'version', name='_app_version_uc'),)

    id = Column(types.Integer, primary_key=True)
    version = Column(types.Integer, nullable=False)

    valid_from = Column(types.DateTime, default=dt.datetime.now, nullable=False)
    price_standard = Column(types.Integer)
    price_priority = Column(types.Integer)
    price_express = Column(types.Integer)
    price_research = Column(types.Integer)
    comment = Column(types.Text)

    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)
    application_id = Column(ForeignKey(Application.id), nullable=False)
    samples = orm.relationship('Sample', backref='application_version')
    pools = orm.relationship('Pool', backref='application_version')

    def __str__(self) -> str:
        return f"{self.application.tag} ({self.version})"


class Panel(Model):

    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(64), unique=True)
    abbrev = Column(types.String(32), unique=True)
    current_version = Column(types.Float, nullable=False)
    date = Column(types.DateTime, nullable=False)
    gene_count = Column(types.Integer)

    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    customer = orm.relationship(Customer, backref='panels')

    def __str__(self):
        return f"{self.abbrev} ({self.current_version})"


class Invoice(Model):

    id = Column(types.Integer, primary_key=True)
    customer_id = Column(ForeignKey('customer.id'), nullable=False)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)
    invoiced_at = Column(types.DateTime)
    comment = Column(types.Text)
    discount = Column(types.Integer, default=0)
    excel_kth = Column(types.BLOB)
    excel_ki = Column(types.BLOB)
    price = Column(types.Integer)
    record_type = Column(types.Text)

    samples = orm.relationship(Sample, backref='invoice')
    pools = orm.relationship(Pool, backref='invoice')
    customer = orm.relationship(Customer, backref='invoices')


class SampleStats(Model):

    id = Column(types.Integer, primary_key=True)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)
    sample_id = Column(ForeignKey(Sample.id), nullable=False, unique=True)
    analysis_id = Column(ForeignKey(Analysis.id), nullable=False)

    # pre-sequencing lab stuff
    capture_kit = Column(types.String(32))
    library_kit_lot_1 = Column(types.String(32))
    library_kit_lot_2 = Column(types.String(32))
    # can sometimes be a mix of two kits
    baits_lot = Column(types.String(64))
    beads_t1_lot = Column(types.String(32))
    fragment_size = Column(types.Integer)
    dna_concentration = Column(types.Float)
    input_material = Column(types.Float)
    index_sequence = Column(types.String(32))

    # mapping/alignment
    reads_total = Column(types.Integer)
    mapped_percent = Column(types.Float)
    duplicates_percent = Column(types.Float)
    strand_balance = Column(types.Float)

    # coverage
    target_coverage = Column(types.Float)
    completeness_target_10 = Column(types.Float)
    completeness_target_20 = Column(types.Float)
    completeness_target_50 = Column(types.Float)
    completeness_target_100 = Column(types.Float)

    # OMIM stats
    # 10-100X completeness

    # variant calling
    variants = Column(types.Integer)  # WHERE?
    indels = Column(types.Integer)
    snps = Column(types.Integer)
    novel_sites = Column(types.Integer)  # WHERE?
    concordant_rate = Column(types.Float)
    hethom_ratio = Column(types.Float)
    titv_ratio = Column(types.Float)

    sample = orm.relationship(Sample, backref='stats', uselist=False)
    analysis = orm.relationship(Analysis, backref='stats')

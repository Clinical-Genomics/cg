# -*- coding: utf-8 -*-
import datetime as dt
from typing import List

import alchy
from sqlalchemy import Column, ForeignKey, orm, types, UniqueConstraint, Table

from cg.constants import (
    REV_PRIORITY_MAP,
    PRIORITY_MAP,
    FAMILY_ACTIONS,
    FLOWCELL_STATUS,
    PREP_CATEGORIES,
)

Model = alchy.make_declarative_base(Base=alchy.ModelBase)


flowcell_sample = Table(
    "flowcell_sample",
    Model.metadata,
    Column("flowcell_id", types.Integer, ForeignKey("flowcell.id"), nullable=False),
    Column("sample_id", types.Integer, ForeignKey("sample.id"), nullable=False),
    UniqueConstraint("flowcell_id", "sample_id", name="_flowcell_sample_uc"),
)


flowcell_microbial_sample = Table(
    "flowcell_microbial_sample",
    Model.metadata,
    Column("flowcell_id", types.Integer, ForeignKey("flowcell.id"), nullable=False),
    Column(
        "microbial_sample_id", types.Integer, ForeignKey("microbial_sample.id"), nullable=False,
    ),
    UniqueConstraint("flowcell_id", "microbial_sample_id", name="_flowcell_microbial_sample_uc"),
)


class PriorityMixin:
    @property
    def priority_human(self):
        """Humanized priority for sample."""
        return REV_PRIORITY_MAP[self.priority]

    @priority_human.setter
    def priority_human(self, priority_str: str):
        self.priority = PRIORITY_MAP.get(priority_str)

    @property
    def high_priority(self):
        """Has high priority?"""
        return self.priority > 1

    @property
    def low_priority(self):
        """Has low priority?"""
        return self.priority < 1


class Application(Model):
    id = Column(types.Integer, primary_key=True)
    tag = Column(types.String(32), unique=True, nullable=False)
    # DEPRECATED, use prep_category instead
    category = Column(types.Enum("wgs", "wes", "tga", "rna", "mic", "rml"))
    prep_category = Column(types.Enum(*PREP_CATEGORIES), nullable=False)
    is_external = Column(types.Boolean, nullable=False, default=False)
    description = Column(types.String(256), nullable=False)
    is_accredited = Column(types.Boolean, nullable=False)

    turnaround_time = Column(types.Integer)
    minimum_order = Column(types.Integer, default=1)
    sequencing_depth = Column(types.Integer)
    min_sequencing_depth = Column(types.Integer)
    target_reads = Column(types.BigInteger, default=0)
    sample_amount = Column(types.Integer)
    sample_volume = Column(types.Text)
    sample_concentration = Column(types.Text)
    priority_processing = Column(types.Boolean, default=False)
    details = Column(types.Text)
    limitations = Column(types.Text)
    percent_kth = Column(types.Integer, nullable=False)
    comment = Column(types.Text)
    is_archived = Column(types.Boolean, default=False)

    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)
    versions = orm.relationship(
        "ApplicationVersion", order_by="ApplicationVersion.version", backref="application",
    )

    def __str__(self) -> str:
        return self.tag

    @property
    def reduced_price(self):
        return self.tag.startswith("WGT") or self.tag.startswith("EXT")

    @property
    def expected_reads(self):
        return self.target_reads * 0.75

    @property
    def analysis_type(self):

        if self.prep_category == "wts":
            return self.prep_category

        return "wgs" if self.prep_category == "wgs" else "wes"


class ApplicationVersion(Model):
    __table_args__ = (UniqueConstraint("application_id", "version", name="_app_version_uc"),)

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
    samples = orm.relationship("Sample", backref="application_version")
    pools = orm.relationship("Pool", backref="application_version")
    microbial_samples = orm.relationship("MicrobialSample", backref="application_version")

    def __str__(self) -> str:
        return f"{self.application.tag} ({self.version})"

    def to_dict(self, application: bool = True):
        """Override dictify method."""
        data = super(ApplicationVersion, self).to_dict()
        if application:
            data["application"] = self.application.to_dict()
        return data


class Analysis(Model):
    id = Column(types.Integer, primary_key=True)
    pipeline = Column(types.String(32), nullable=False)
    pipeline_version = Column(types.String(32))
    started_at = Column(types.DateTime)
    completed_at = Column(types.DateTime)
    delivery_report_created_at = Column(types.DateTime)
    upload_started_at = Column(types.DateTime)
    uploaded_at = Column(types.DateTime)
    cleaned_at = Column(types.DateTime)
    # primary analysis is the one originally delivered to the customer
    is_primary = Column(types.Boolean, default=False)

    created_at = Column(types.DateTime, default=dt.datetime.now, nullable=False)
    family_id = Column(ForeignKey("family.id", ondelete="CASCADE"))
    microbial_order_id = Column(ForeignKey("microbial_order.id", ondelete="CASCADE"))

    def __str__(self):
        return f"{self.family.internal_id} | {self.completed_at.date()}"

    def to_dict(self, family: bool = True):
        """Override dictify method."""
        data = super(Analysis, self).to_dict()
        if family:
            data["family"] = self.family.to_dict()
        return data


class Bed(Model):
    """Model for bed target captures """

    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(32), unique=True, nullable=False)
    comment = Column(types.Text)
    is_archived = Column(types.Boolean, default=False)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)

    versions = orm.relationship("BedVersion", order_by="BedVersion.version", backref="bed")

    def __str__(self) -> str:
        return self.name


class BedVersion(Model):
    """Model for bed target captures versions """

    __table_args__ = (UniqueConstraint("bed_id", "version", name="_app_version_uc"),)

    id = Column(types.Integer, primary_key=True)
    shortname = Column(types.String(64))
    version = Column(types.Integer, nullable=False)
    filename = Column(types.String(256), nullable=False)
    checksum = Column(types.String(32))
    panel_size = Column(types.Integer)
    genome_version = Column(types.String(32))
    designer = Column(types.String(256))
    comment = Column(types.Text)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)
    bed_id = Column(ForeignKey(Bed.id), nullable=False)

    def __str__(self) -> str:
        return f"{self.bed.name} ({self.version})"

    def to_dict(self, bed: bool = True):
        """Override dictify method."""
        data = super(BedVersion, self).to_dict()
        if bed:
            data["bed"] = self.bed.to_dict()
        return data


class Customer(Model):
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)
    priority = Column(types.Enum("diagnostic", "research"))
    scout_access = Column(types.Boolean, nullable=False, default=False)
    loqus_upload = Column(types.Boolean, nullable=False, default=False)
    return_samples = Column(types.Boolean, nullable=False, default=False)

    agreement_date = Column(types.DateTime)
    agreement_registration = Column(types.String(32))
    project_account_ki = Column(types.String(32))
    project_account_kth = Column(types.String(32))
    organisation_number = Column(types.String(32))
    invoice_address = Column(types.Text, nullable=False)
    invoice_reference = Column(types.String(32), nullable=False)
    uppmax_account = Column(types.String(32))
    comment = Column(types.Text)

    primary_contact_id = Column(ForeignKey("user.id"))
    primary_contact = orm.relationship("User", foreign_keys=[primary_contact_id])
    delivery_contact_id = Column(ForeignKey("user.id"))
    delivery_contact = orm.relationship("User", foreign_keys=[delivery_contact_id])
    invoice_contact_id = Column(ForeignKey("user.id"))
    invoice_contact = orm.relationship("User", foreign_keys=[invoice_contact_id])
    customer_group_id = Column(ForeignKey("customer_group.id"), nullable=False)

    families = orm.relationship("Family", backref="customer", order_by="-Family.id")
    samples = orm.relationship("Sample", backref="customer", order_by="-Sample.id")
    pools = orm.relationship("Pool", backref="customer", order_by="-Pool.id")
    orders = orm.relationship("MicrobialOrder", backref="customer", order_by="-MicrobialOrder.id")

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"


class CustomerGroup(Model):
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)

    customers = orm.relationship("Customer", backref="customer_group", order_by="-Customer.id")

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"


class Delivery(Model):
    id = Column(types.Integer, primary_key=True)
    delivered_at = Column(types.DateTime)
    removed_at = Column(types.DateTime)
    destination = Column(types.Enum("caesar", "pdc", "uppmax", "mh", "custom"), default="caesar")
    sample_id = Column(ForeignKey("sample.id", ondelete="CASCADE"))
    pool_id = Column(ForeignKey("pool.id", ondelete="CASCADE"))
    comment = Column(types.Text)


class Family(Model, PriorityMixin):
    __table_args__ = (UniqueConstraint("customer_id", "name", name="_customer_name_uc"),)

    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)
    priority = Column(types.Integer, default=1, nullable=False)
    _panels = Column(types.Text)
    action = Column(types.Enum(*FAMILY_ACTIONS))
    comment = Column(types.Text)

    ordered_at = Column(types.DateTime, default=dt.datetime.now)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    customer_id = Column(ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    analyses = orm.relationship("Analysis", backref="family", order_by="-Analysis.completed_at")

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    def to_dict(self, links: bool = False, analyses: bool = False) -> dict:
        """Override dictify method."""
        data = super(Family, self).to_dict()
        data["panels"] = self.panels
        data["priority"] = self.priority_human
        data["customer"] = self.customer.to_dict()
        if links:
            data["links"] = [link_obj.to_dict(samples=True) for link_obj in self.links]
        if analyses:
            data["analyses"] = [
                analysis_obj.to_dict(family=False) for analysis_obj in self.analyses
            ]
        return data

    @property
    def panels(self) -> List[str]:
        """Return a list of panels."""
        panel_list = self._panels.split(",") if self._panels else []
        return panel_list

    @panels.setter
    def panels(self, panel_list: List[str]):
        self._panels = ",".join(panel_list) if panel_list else None


class FamilySample(Model):
    __table_args__ = (UniqueConstraint("family_id", "sample_id", name="_family_sample_uc"),)

    id = Column(types.Integer, primary_key=True)
    family_id = Column(ForeignKey("family.id", ondelete="CASCADE"), nullable=False)
    sample_id = Column(ForeignKey("sample.id", ondelete="CASCADE"), nullable=False)
    status = Column(
        types.Enum("affected", "unaffected", "unknown"), default="unknown", nullable=False,
    )

    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)

    mother_id = Column(ForeignKey("sample.id"))
    father_id = Column(ForeignKey("sample.id"))

    family = orm.relationship("Family", backref="links")
    sample = orm.relationship("Sample", foreign_keys=[sample_id], backref="links")
    mother = orm.relationship("Sample", foreign_keys=[mother_id])
    father = orm.relationship("Sample", foreign_keys=[father_id])

    def to_dict(self, parents: bool = False, samples: bool = False, family: bool = False) -> dict:
        """Override dictify method."""
        data = super(FamilySample, self).to_dict()
        if samples:
            data["sample"] = self.sample.to_dict()
            data["mother"] = self.mother.to_dict() if self.mother else None
            data["father"] = self.father.to_dict() if self.father else None
        elif parents:
            data["mother"] = self.mother.to_dict() if self.mother else None
            data["father"] = self.father.to_dict() if self.father else None
        if family:
            data["family"] = self.family.to_dict()
        return data

    def __str__(self) -> str:
        return f"{self.family.internal_id} | {self.sample.internal_id}"


class Flowcell(Model):
    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(32), unique=True, nullable=False)
    sequencer_type = Column(types.Enum("hiseqga", "hiseqx", "novaseq"))
    sequencer_name = Column(types.String(32))
    sequenced_at = Column(types.DateTime)
    status = Column(types.Enum(*FLOWCELL_STATUS), default="ondisk")
    archived_at = Column(types.DateTime)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)

    samples = orm.relationship("Sample", secondary=flowcell_sample, backref="flowcells")
    microbial_samples = orm.relationship(
        "MicrobialSample", secondary=flowcell_microbial_sample, backref="flowcells"
    )

    def __str__(self):
        return self.name

    def to_dict(self, samples: bool = False, microbial_samples: bool = False):
        """Override dictify method."""
        data = super(Flowcell, self).to_dict()
        if samples:
            data["samples"] = [sample.to_dict() for sample in self.samples]
        if microbial_samples:
            data["microbial_samples"] = [sample.to_dict() for sample in self.microbial_samples]
        return data


class MicrobialOrder(Model):
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True)
    name = Column(types.String(128), nullable=False)
    ticket_number = Column(types.Integer)
    comment = Column(types.Text)

    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)
    ordered_at = Column(types.DateTime, nullable=False)

    customer_id = Column(ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    microbial_samples = orm.relationship(
        "MicrobialSample", backref="microbial_order", order_by="-MicrobialSample.delivered_at",
    )
    analyses = orm.relationship(
        "Analysis", backref="microbial_order", order_by="-Analysis.completed_at"
    )

    def __str__(self):
        return f"{self.internal_id} ({self.name})"

    def to_dict(self, samples: bool = False) -> dict:
        """Override dictify method."""
        data = super(MicrobialOrder, self).to_dict()
        data["customer"] = self.customer.to_dict()
        if samples:
            data["microbial_samples"] = [
                microbial_samples_obj.to_dict() for microbial_samples_obj in self.microbial_samples
            ]
        return data


class MicrobialSample(Model, PriorityMixin):
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), nullable=False, unique=True)
    name = Column(types.String(128), nullable=False)
    data_analysis = Column(types.String(16))
    application_version_id = Column(ForeignKey("application_version.id"), nullable=False)
    microbial_order_id = Column(ForeignKey("microbial_order.id"), nullable=False)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)
    received_at = Column(types.DateTime)
    prepared_at = Column(types.DateTime)
    sequence_start = Column(types.DateTime)
    sequenced_at = Column(types.DateTime)
    delivered_at = Column(types.DateTime)
    organism_id = Column(ForeignKey("organism.id"))
    organism = orm.relationship("Organism", foreign_keys=[organism_id])

    reference_genome = Column(types.String(255))

    priority = Column(types.Integer, default=1, nullable=False)
    reads = Column(types.BigInteger, default=0)
    comment = Column(types.Text)
    invoice_id = Column(ForeignKey("invoice.id"))

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    @property
    def state(self) -> str:
        """Get the current microbial sample state."""
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

    def to_dict(self, order=False) -> dict:
        """Override dictify method."""
        data = super(MicrobialSample, self).to_dict()
        data["application_version"] = self.application_version.to_dict()
        data["application"] = self.application_version.application.to_dict()
        data["priority"] = self.priority_human
        if order:
            data["microbial_order"] = self.microbial_order.to_dict()
        if self.invoice_id:
            data["invoice"] = self.invoice.to_dict()
        if self.organism_id:
            data["organism"] = self.organism.to_dict()
        return data


class Organism(Model):
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), nullable=False, unique=True)
    name = Column(types.String(255), nullable=False, unique=True)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)
    reference_genome = Column(types.String(255))
    verified = Column(types.Boolean, default=False)
    comment = Column(types.Text)

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    def to_dict(self) -> dict:
        """Override dictify method."""
        data = super(Organism, self).to_dict()
        return data


class Panel(Model):
    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(64), unique=True)
    abbrev = Column(types.String(32), unique=True)
    current_version = Column(types.Float, nullable=False)
    date = Column(types.DateTime, nullable=False)
    gene_count = Column(types.Integer)

    customer_id = Column(ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    customer = orm.relationship(Customer, backref="panels")

    def __str__(self):
        return f"{self.abbrev} ({self.current_version})"


class Pool(Model):
    __table_args__ = (UniqueConstraint("order", "name", name="_order_name_uc"),)

    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(32), nullable=False)
    data_analysis = Column(types.String(16))
    order = Column(types.String(64), nullable=False)
    ticket_number = Column(types.Integer)
    reads = Column(types.BigInteger, default=0)
    ordered_at = Column(types.DateTime, nullable=False)
    received_at = Column(types.DateTime)
    sequenced_at = Column(types.DateTime)
    delivered_at = Column(types.DateTime)
    invoice_id = Column(ForeignKey("invoice.id"))
    invoiced_at = Column(types.DateTime)  # DEPRECATED
    comment = Column(types.Text)
    lims_project = Column(types.Text)
    no_invoice = Column(types.Boolean, default=False)
    capture_kit = Column(types.String(64))

    created_at = Column(types.DateTime, default=dt.datetime.now)
    customer_id = Column(ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    application_version_id = Column(ForeignKey("application_version.id"), nullable=False)

    deliveries = orm.relationship("Delivery", backref="pool")


class Sample(Model, PriorityMixin):

    application_version_id = Column(ForeignKey("application_version.id"), nullable=False)
    beaconized_at = Column(types.Text)
    capture_kit = Column(types.String(64))
    comment = Column(types.Text)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    customer_id = Column(ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    data_analysis = Column(types.String(16))
    delivered_at = Column(types.DateTime)
    deliveries = orm.relationship("Delivery", backref="sample")
    downsampled_to = Column(types.BigInteger)
    from_sample = Column(types.String(128))
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), nullable=False, unique=True)
    invoice_id = Column(ForeignKey("invoice.id"))
    invoiced_at = Column(types.DateTime)  # DEPRECATED
    is_external = Column(types.Boolean, default=False)  # DEPRECATED
    is_tumour = Column(types.Boolean, default=False)
    loqusdb_id = Column(types.String(64))
    name = Column(types.String(128), nullable=False)
    no_invoice = Column(types.Boolean, default=False)
    order = Column(types.String(64))
    ordered_at = Column(types.DateTime, nullable=False)
    prepared_at = Column(types.DateTime)
    priority = Column(types.Integer, default=1, nullable=False)
    reads = Column(types.BigInteger, default=0)
    received_at = Column(types.DateTime)
    sequence_start = Column(types.DateTime)
    sequenced_at = Column(types.DateTime)
    sex = Column(types.Enum("male", "female", "unknown"), nullable=False)
    ticket_number = Column(types.Integer)
    time_point = Column(types.Integer)

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

    def to_dict(self, links: bool = False, flowcells: bool = False) -> dict:
        """Override dictify method."""
        data = super(Sample, self).to_dict()
        data["priority"] = self.priority_human
        data["customer"] = self.customer.to_dict()
        data["application_version"] = self.application_version.to_dict()
        data["application"] = self.application_version.application.to_dict()
        if links:
            data["links"] = [link_obj.to_dict(family=True, parents=True) for link_obj in self.links]
        if flowcells:
            data["flowcells"] = [flowcell_obj.to_dict() for flowcell_obj in self.flowcells]
        return data


class Invoice(Model):
    id = Column(types.Integer, primary_key=True)
    customer_id = Column(ForeignKey("customer.id"), nullable=False)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)
    invoiced_at = Column(types.DateTime)
    comment = Column(types.Text)
    discount = Column(types.Integer, default=0)
    excel_kth = Column(types.BLOB)
    excel_ki = Column(types.BLOB)
    price = Column(types.Integer)
    record_type = Column(types.Text)

    samples = orm.relationship(Sample, backref="invoice")
    microbial_samples = orm.relationship(MicrobialSample, backref="invoice")
    pools = orm.relationship(Pool, backref="invoice")
    customer = orm.relationship(Customer, backref="invoices")

    def __str__(self):
        return f"{self.customer_id} ({self.invoiced_at})"

    def to_dict(self) -> dict:
        """Override dictify method."""
        data = super(Invoice, self).to_dict()
        return data


class User(Model):
    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(128), nullable=False)
    email = Column(types.String(128), unique=True, nullable=False)
    is_admin = Column(types.Boolean, default=False)

    customer_id = Column(
        ForeignKey("customer.id", ondelete="CASCADE", use_alter=True), nullable=False
    )
    customer = orm.relationship("Customer", foreign_keys=[customer_id])

    def to_dict(self) -> dict:
        """Override dictify method."""
        data = super(User, self).to_dict()
        data["customer"] = self.customer.to_dict()
        return data

    def __str__(self) -> str:
        return self.name

import datetime as dt
from typing import List, Optional

import alchy
from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint, orm, types

from cg.constants import (
    CASE_ACTIONS,
    FLOWCELL_STATUS,
    PREP_CATEGORIES,
    PRIORITY_MAP,
    REV_PRIORITY_MAP,
    SEX_OPTIONS,
    STATUS_OPTIONS,
    DataDelivery,
    Pipeline,
)
from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint, orm, types

Model = alchy.make_declarative_base(Base=alchy.ModelBase)


flowcell_sample = Table(
    "flowcell_sample",
    Model.metadata,
    Column("flowcell_id", types.Integer, ForeignKey("flowcell.id"), nullable=False),
    Column("sample_id", types.Integer, ForeignKey("sample.id"), nullable=False),
    UniqueConstraint("flowcell_id", "sample_id", name="_flowcell_sample_uc"),
)

customer_user = Table(
    "customer_user",
    Model.metadata,
    Column("customer_id", types.Integer, ForeignKey("customer.id"), nullable=False),
    Column("user_id", types.Integer, ForeignKey("user.id"), nullable=False),
    UniqueConstraint("customer_id", "user_id", name="_customer_user_uc"),
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
    prep_category = Column(types.Enum(*PREP_CATEGORIES), nullable=False)
    is_external = Column(types.Boolean, nullable=False, default=False)
    description = Column(types.String(256), nullable=False)
    is_accredited = Column(types.Boolean, nullable=False)

    turnaround_time = Column(types.Integer)
    minimum_order = Column(types.Integer, default=1)
    sequencing_depth = Column(types.Integer)
    min_sequencing_depth = Column(types.Integer)
    target_reads = Column(types.BigInteger, default=0)
    percent_reads_guaranteed = Column(types.Integer, nullable=False)
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
        "ApplicationVersion", order_by="ApplicationVersion.version", backref="application"
    )

    def __str__(self) -> str:
        return self.tag

    @property
    def reduced_price(self):
        return self.tag.startswith("WGT") or self.tag.startswith("EXT")

    @property
    def expected_reads(self):
        return self.target_reads * self.percent_reads_guaranteed / 100

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

    def __str__(self) -> str:
        return f"{self.application.tag} ({self.version})"

    def to_dict(self, application: bool = True):
        """Represent as dictionary"""
        data = super(ApplicationVersion, self).to_dict()
        if application:
            data["application"] = self.application.to_dict()
        return data


class Analysis(Model):
    id = Column(types.Integer, primary_key=True)
    pipeline = Column(types.Enum(*list(Pipeline)))
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
    uploaded_to_vogue_at = Column(types.DateTime, nullable=True)

    def __str__(self):
        return f"{self.family.internal_id} | {self.completed_at.date()}"

    def to_dict(self, family: bool = True):
        """Represent as dictionary"""
        data = super(Analysis, self).to_dict()
        if family:
            data["family"] = self.family.to_dict()
        return data


class Bed(Model):
    """Model for bed target captures"""

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
    """Model for bed target captures versions"""

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
        """Represent as dictionary"""
        data = super(BedVersion, self).to_dict()
        if bed:
            data["bed"] = self.bed.to_dict()
        return data


class Customer(Model):

    agreement_date = Column(types.DateTime)
    agreement_registration = Column(types.String(32))
    comment = Column(types.Text)
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    invoice_address = Column(types.Text, nullable=False)
    invoice_reference = Column(types.String(32), nullable=False)
    loqus_upload = Column(types.Boolean, nullable=False, default=False)
    name = Column(types.String(128), nullable=False)
    organisation_number = Column(types.String(32))
    priority = Column(types.Enum("diagnostic", "research"))
    project_account_ki = Column(types.String(32))
    project_account_kth = Column(types.String(32))
    return_samples = Column(types.Boolean, nullable=False, default=False)
    scout_access = Column(types.Boolean, nullable=False, default=False)
    uppmax_account = Column(types.String(32))

    customer_group_id = Column(ForeignKey("customer_group.id"), nullable=False)
    delivery_contact_id = Column(ForeignKey("user.id"))
    delivery_contact = orm.relationship("User", foreign_keys=[delivery_contact_id])
    invoice_contact_id = Column(ForeignKey("user.id"))
    invoice_contact = orm.relationship("User", foreign_keys=[invoice_contact_id])
    primary_contact_id = Column(ForeignKey("user.id"))
    primary_contact = orm.relationship("User", foreign_keys=[primary_contact_id])

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"


class CustomerGroup(Model):
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)

    customers = orm.relationship(Customer, backref="customer_group", order_by="-Customer.id")

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

    action = Column(types.Enum(*CASE_ACTIONS))
    analyses = orm.relationship(Analysis, backref="family", order_by="-Analysis.completed_at")
    avatar_url = Column(types.Text)
    _cohorts = Column(types.Text)
    comment = Column(types.Text)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    customer_id = Column(ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    customer = orm.relationship(Customer, foreign_keys=[customer_id])
    data_analysis = Column(types.Enum(*list(Pipeline)))
    data_delivery = Column(types.Enum(*list(DataDelivery)))
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)
    ordered_at = Column(types.DateTime, default=dt.datetime.now)
    _panels = Column(types.Text)
    priority = Column(types.Integer, default=1, nullable=False)
    _synopsis = Column(types.Text)

    @property
    def cohorts(self) -> List[str]:
        """Return a list of cohorts."""
        return self._cohorts.split(",") if self._cohorts else []

    @cohorts.setter
    def cohorts(self, cohort_list: List[str]):
        self._cohorts = ",".join(cohort_list) if cohort_list else None

    @property
    def panels(self) -> List[str]:
        """Return a list of panels."""
        return self._panels.split(",") if self._panels else []

    @panels.setter
    def panels(self, panel_list: List[str]):
        self._panels = ",".join(panel_list) if panel_list else None

    @property
    def synopsis(self) -> List[str]:
        """Return a list of synopsis."""
        return self._synopsis.split(",") if self._synopsis else []

    @synopsis.setter
    def synopsis(self, synopsis_list: List[str]):
        self._synopsis = ",".join(synopsis_list) if synopsis_list else None

    @property
    def latest_analyzed(self) -> Optional[dt.datetime]:
        return self.analyses[0].completed_at if self.analyses else None

    @property
    def latest_sequenced(self) -> Optional[dt.datetime]:
        sequenced_dates = []
        for link in self.links:
            if link.sample.is_external:
                sequenced_dates.append(link.sample.ordered_at)
            elif link.sample.sequenced_at:
                sequenced_dates.append(link.sample.sequenced_at)
        return max(sequenced_dates) if sequenced_dates else None

    @property
    def all_samples_pass_qc(self) -> bool:
        pass_qc = []
        for link in self.links:
            if link.sample.is_external or link.sample.sequencing_qc:
                pass_qc.append(True)
            else:
                pass_qc.append(False)
        return all(pass_qc)

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    def to_dict(self, links: bool = False, analyses: bool = False) -> dict:
        """Represent as dictionary"""
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


class FamilySample(Model):
    __table_args__ = (UniqueConstraint("family_id", "sample_id", name="_family_sample_uc"),)

    id = Column(types.Integer, primary_key=True)
    family_id = Column(ForeignKey("family.id", ondelete="CASCADE"), nullable=False)
    sample_id = Column(ForeignKey("sample.id", ondelete="CASCADE"), nullable=False)
    status = Column(types.Enum(*STATUS_OPTIONS), default="unknown", nullable=False)

    created_at = Column(types.DateTime, default=dt.datetime.now)
    updated_at = Column(types.DateTime, onupdate=dt.datetime.now)

    mother_id = Column(ForeignKey("sample.id"))
    father_id = Column(ForeignKey("sample.id"))

    family = orm.relationship("Family", backref="links")
    sample = orm.relationship("Sample", foreign_keys=[sample_id], backref="links")
    mother = orm.relationship("Sample", foreign_keys=[mother_id], backref="mother_links")
    father = orm.relationship("Sample", foreign_keys=[father_id], backref="father_links")

    def to_dict(self, parents: bool = False, samples: bool = False, family: bool = False) -> dict:
        """Represent as dictionary"""
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

    def __str__(self):
        return self.name

    def to_dict(self, samples: bool = False):
        """Represent as dictionary"""
        data = super(Flowcell, self).to_dict()
        if samples:
            data["samples"] = [sample.to_dict() for sample in self.samples]
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
        """Represent as dictionary"""
        return super(Organism, self).to_dict()


class Panel(Model):

    abbrev = Column(types.String(32), unique=True)
    current_version = Column(types.Float, nullable=False)
    customer_id = Column(ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    customer = orm.relationship(Customer, backref="panels")
    date = Column(types.DateTime, nullable=False)
    gene_count = Column(types.Integer)
    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(64), unique=True)

    def __str__(self):
        return f"{self.abbrev} ({self.current_version})"


class Pool(Model):
    __table_args__ = (UniqueConstraint("order", "name", name="_order_name_uc"),)

    application_version_id = Column(ForeignKey("application_version.id"), nullable=False)
    application_version = orm.relationship(
        ApplicationVersion, foreign_keys=[application_version_id]
    )
    comment = Column(types.Text)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    customer_id = Column(ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    customer = orm.relationship(Customer, foreign_keys=[customer_id])
    delivered_at = Column(types.DateTime)
    deliveries = orm.relationship(Delivery, backref="pool")
    id = Column(types.Integer, primary_key=True)
    invoice_id = Column(ForeignKey("invoice.id"))
    name = Column(types.String(32), nullable=False)
    no_invoice = Column(types.Boolean, default=False)
    order = Column(types.String(64), nullable=False)
    ordered_at = Column(types.DateTime, nullable=False)
    received_at = Column(types.DateTime)
    ticket_number = Column(types.Integer)


class Sample(Model, PriorityMixin):

    age_at_sampling = Column(types.FLOAT)
    application_version_id = Column(ForeignKey("application_version.id"), nullable=False)
    application_version = orm.relationship(
        ApplicationVersion, foreign_keys=[application_version_id]
    )
    capture_kit = Column(types.String(64))
    comment = Column(types.Text)
    created_at = Column(types.DateTime, default=dt.datetime.now)
    customer_id = Column(ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    customer = orm.relationship("Customer", foreign_keys=[customer_id])
    delivered_at = Column(types.DateTime)
    deliveries = orm.relationship(Delivery, backref="sample")
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
    organism_id = Column(ForeignKey("organism.id"))
    organism = orm.relationship("Organism", foreign_keys=[organism_id])
    _phenotype_terms = Column(types.Text)
    prepared_at = Column(types.DateTime)
    priority = Column(types.Integer, default=1, nullable=False)
    reads = Column(types.BigInteger, default=0)
    received_at = Column(types.DateTime)
    reference_genome = Column(types.String(255))
    sequence_start = Column(types.DateTime)
    sequenced_at = Column(types.DateTime)
    sex = Column(types.Enum(*SEX_OPTIONS), nullable=False)
    ticket_number = Column(types.Integer)
    time_point = Column(types.Integer)

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    @property
    def sequencing_qc(self) -> bool:
        """Return sequencing qc passed or failed."""
        application = self.application_version.application
        return self.reads > application.expected_reads

    @property
    def phenotype_terms(self) -> List[str]:
        """Return a list of phenotype_terms."""
        return self._phenotype_terms.split(",") if self._phenotype_terms else []

    @phenotype_terms.setter
    def phenotype_terms(self, phenotype_term_list: List[str]):
        self._phenotype_terms = ",".join(phenotype_term_list) if phenotype_term_list else None

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
        """Represent as dictionary"""
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
    customer = orm.relationship(Customer, foreign_keys=[customer_id])
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
    pools = orm.relationship(Pool, backref="invoice")

    def __str__(self):
        return f"{self.customer_id} ({self.invoiced_at})"

    def to_dict(self) -> dict:
        """Represent as dictionary"""
        return super(Invoice, self).to_dict()


class User(Model):
    id = Column(types.Integer, primary_key=True)
    name = Column(types.String(128), nullable=False)
    email = Column(types.String(128), unique=True, nullable=False)
    is_admin = Column(types.Boolean, default=False)
    order_portal_login = Column(types.Boolean, default=False)

    customers = orm.relationship("Customer", secondary=customer_user, backref="users")

    def to_dict(self) -> dict:
        """Represent as dictionary"""
        data = super(User, self).to_dict()
        data["customers"] = [record.to_dict() for record in self.customers]
        return data

    def __str__(self) -> str:
        return self.name

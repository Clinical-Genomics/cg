import re
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint, orm, types
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.util import deprecated

from cg.constants import DataDelivery, FlowCellStatus, Priority, Workflow
from cg.constants.archiving import PDC_ARCHIVE_LOCATION
from cg.constants.constants import (
    CaseActions,
    ControlOptions,
    PrepCategory,
    SexOptions,
    StatusOptions,
)
from cg.constants.priority import SlurmQos


class Base(DeclarativeBase):
    pass


def to_dict(model_instance):
    if hasattr(model_instance, "__table__"):
        return {
            column.name: getattr(model_instance, column.name)
            for column in model_instance.__table__.columns
            if not isinstance(getattr(model_instance, column.name), InstrumentedAttribute)
        }


flowcell_sample = Table(
    "flowcell_sample",
    Base.metadata,
    Column("flowcell_id", types.Integer, ForeignKey("flowcell.id"), nullable=False),
    Column("sample_id", types.Integer, ForeignKey("sample.id"), nullable=False),
    UniqueConstraint("flowcell_id", "sample_id", name="_flowcell_sample_uc"),
)

customer_user = Table(
    "customer_user",
    Base.metadata,
    Column("customer_id", types.Integer, ForeignKey("customer.id"), nullable=False),
    Column("user_id", types.Integer, ForeignKey("user.id"), nullable=False),
    UniqueConstraint("customer_id", "user_id", name="_customer_user_uc"),
)

customer_collaboration = Table(
    "customer_collaboration",
    Base.metadata,
    Column("customer_id", types.Integer, ForeignKey("customer.id"), nullable=False),
    Column("collaboration_id", types.Integer, ForeignKey("collaboration.id"), nullable=False),
    UniqueConstraint("customer_id", "collaboration_id", name="_customer_collaboration_uc"),
)


class PriorityMixin:
    @property
    def priority_human(self) -> str:
        """Humanized priority for sample."""
        return self.priority.name

    @priority_human.setter
    def priority_human(self, priority: str) -> None:
        self.priority: Priority = Priority[priority]

    @property
    def priority_int(self) -> int:
        """Priority as integer for sample."""
        return self.priority.value

    @priority_int.setter
    def priority_int(self, priority_int: int) -> None:
        self.priority: Priority = Priority(priority_int)

    @property
    def high_priority(self):
        """Has high priority?"""
        return self.priority_int > 1

    @property
    def low_priority(self):
        """Has low priority?"""
        return self.priority_int < 1


class Application(Base):
    __tablename__ = "application"

    id: Mapped[int] = mapped_column(types.Integer, primary_key=True)
    tag: Mapped[str] = mapped_column(types.String(32), unique=True, nullable=False)
    prep_category: Mapped[str] = mapped_column(types.Enum(*PrepCategory), nullable=False)
    is_external: Mapped[bool] = mapped_column(types.Boolean, nullable=False, default=False)
    description: Mapped[str] = mapped_column(types.String(256), nullable=False)
    is_accredited: Mapped[bool] = mapped_column(types.Boolean, nullable=False)

    turnaround_time: Mapped[Optional[int]] = mapped_column(types.Integer)
    minimum_order: Mapped[Optional[int]] = mapped_column(types.Integer, default=1)
    sequencing_depth: Mapped[Optional[int]] = mapped_column(types.Integer)
    min_sequencing_depth: Mapped[int] = mapped_column(types.Integer, default=0, nullable=False)
    target_reads: Mapped[Optional[int]] = mapped_column(types.BigInteger, default=0)
    percent_reads_guaranteed: Mapped[int] = mapped_column(types.Integer, nullable=False)
    sample_amount: Mapped[Optional[int]] = mapped_column(types.Integer)
    sample_volume: Mapped[Optional[str]] = mapped_column(types.Text)
    sample_concentration: Mapped[Optional[str]] = mapped_column(types.Text)
    sample_concentration_minimum: Mapped[Optional[float]] = mapped_column(types.DECIMAL)
    sample_concentration_maximum: Mapped[Optional[float]] = mapped_column(types.DECIMAL)
    sample_concentration_minimum_cfdna: Mapped[Optional[float]] = mapped_column(types.DECIMAL)
    sample_concentration_maximum_cfdna: Mapped[Optional[float]] = mapped_column(types.DECIMAL)
    priority_processing: Mapped[bool] = mapped_column(types.Boolean, default=False)
    details: Mapped[Optional[str]] = mapped_column(types.Text)
    limitations: Mapped[Optional[str]] = mapped_column(types.Text)
    percent_kth: Mapped[int] = mapped_column(types.Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(types.Text)
    is_archived: Mapped[bool] = mapped_column(types.Boolean, default=False)

    created_at: Mapped[Optional[datetime]] = mapped_column(types.DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(types.DateTime, onupdate=datetime.now)

    versions: Mapped[list["ApplicationVersion"]] = orm.relationship(
        "ApplicationVersion", order_by="ApplicationVersion.version", back_populates="application"
    )
    pipeline_limitations: Mapped[list["ApplicationLimitations"]] = orm.relationship(
        "ApplicationLimitations", back_populates="application"
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
    def analysis_type(self) -> str:
        if self.prep_category == PrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING.value:
            return PrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING.value

        return (
            PrepCategory.WHOLE_GENOME_SEQUENCING.value
            if self.prep_category == PrepCategory.WHOLE_GENOME_SEQUENCING.value
            else PrepCategory.WHOLE_EXOME_SEQUENCING.value
        )

    def to_dict(self):
        return to_dict(model_instance=self)


class ApplicationVersion(Base):
    __tablename__ = "application_version"
    __table_args__ = (UniqueConstraint("application_id", "version", name="_app_version_uc"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[int]

    valid_from: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    price_standard: Mapped[Optional[int]]
    price_priority: Mapped[Optional[int]]
    price_express: Mapped[Optional[int]]
    price_research: Mapped[Optional[int]]
    price_clinical_trials: Mapped[Optional[int]]
    comment: Mapped[Optional[str]] = mapped_column(types.Text)

    created_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=datetime.now)
    application_id: Mapped[int] = mapped_column(ForeignKey(Application.id))

    application: Mapped["Application"] = orm.relationship(back_populates="versions")

    def __str__(self) -> str:
        return f"{self.application.tag} ({self.version})"

    def to_dict(self, application: bool = True):
        """Represent as dictionary"""
        data = to_dict(model_instance=self)
        if application:
            data["application"] = self.application.to_dict()
        return data


class ApplicationLimitations(Base):
    __tablename__ = "application_limitations"

    id: Mapped[int] = mapped_column(types.Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey(Application.id))
    pipeline: Mapped[Workflow]
    limitations: Mapped[Optional[str]] = mapped_column(types.Text)
    comment: Mapped[Optional[str]] = mapped_column(types.Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=datetime.now)

    application: Mapped["Application"] = orm.relationship(back_populates="pipeline_limitations")

    def __str__(self):
        return f"{self.application.tag} – {self.pipeline}"

    def to_dict(self):
        return to_dict(model_instance=self)


class Analysis(Base):
    __tablename__ = "analysis"

    id: Mapped[int] = mapped_column(types.Integer, primary_key=True)
    pipeline: Mapped[Optional[Workflow]]
    pipeline_version: Mapped[Optional[str]] = mapped_column(types.String(32))
    started_at: Mapped[Optional[datetime]]
    completed_at: Mapped[Optional[datetime]]
    delivery_report_created_at: Mapped[Optional[datetime]]
    upload_started_at: Mapped[Optional[datetime]]
    uploaded_at: Mapped[Optional[datetime]]
    cleaned_at: Mapped[Optional[datetime]]
    # primary analysis is the one originally delivered to the customer
    is_primary: Mapped[Optional[bool]] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    case_id: Mapped[int] = mapped_column(ForeignKey("case.id", ondelete="CASCADE"))

    case: Mapped["Case"] = orm.relationship(back_populates="analyses")

    def __str__(self):
        return f"{self.case.internal_id} | {self.completed_at.date()}"

    def to_dict(self, family: bool = True):
        """Represent as dictionary"""
        data = to_dict(model_instance=self)
        if family:
            data["family"] = self.case.to_dict()
        return data


class Bed(Base):
    """Model for bed target captures"""

    __tablename__ = "bed"
    id: Mapped[int] = mapped_column(types.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(types.String(32), unique=True)
    comment: Mapped[Optional[str]] = mapped_column(types.Text)
    is_archived: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=datetime.now)

    versions: Mapped[list["BedVersion"]] = orm.relationship(
        order_by="BedVersion.version", back_populates="bed"
    )

    def __str__(self) -> str:
        return self.name

    def to_dict(self):
        return to_dict(model_instance=self)


class BedVersion(Base):
    """Model for bed target captures versions"""

    __tablename__ = "bed_version"
    __table_args__ = (UniqueConstraint("bed_id", "version", name="_app_version_uc"),)

    id: Mapped[int] = mapped_column(types.Integer, primary_key=True)
    shortname: Mapped[Optional[str]] = mapped_column(types.String(64))
    version: Mapped[int]
    filename: Mapped[str] = mapped_column(types.String(256))
    checksum: Mapped[Optional[str]] = mapped_column(types.String(32))
    panel_size: Mapped[Optional[int]]
    genome_version: Mapped[Optional[str]] = mapped_column(types.String(32))
    designer: Mapped[Optional[str]] = mapped_column(types.String(256))
    comment: Mapped[Optional[str]] = mapped_column(types.Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=datetime.now)
    bed_id: Mapped[int] = mapped_column(ForeignKey(Bed.id))

    bed: Mapped["Bed"] = orm.relationship(back_populates="versions")

    def __str__(self) -> str:
        return f"{self.bed.name} ({self.version})"

    def to_dict(self, bed: bool = True):
        """Represent as dictionary"""
        data = to_dict(model_instance=self)
        if bed:
            data["bed"] = self.bed.to_dict()
        return data


class Customer(Base):
    __tablename__ = "customer"
    agreement_date: Mapped[Optional[datetime]]
    agreement_registration: Mapped[Optional[str]] = mapped_column(types.String(32))
    comment: Mapped[Optional[str]] = mapped_column(types.Text)
    id: Mapped[int] = mapped_column(types.Integer, primary_key=True)
    internal_id: Mapped[str] = mapped_column(types.String(32), unique=True)
    invoice_address: Mapped[str] = mapped_column(types.Text)
    invoice_reference: Mapped[str] = mapped_column(types.String(32))
    is_trusted: Mapped[bool] = mapped_column(default=False)
    lab_contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    lab_contact: Mapped[Optional["User"]] = orm.relationship(foreign_keys=[lab_contact_id])
    loqus_upload: Mapped[bool] = mapped_column(default=False)
    name: Mapped[str] = mapped_column(types.String(128))
    organisation_number: Mapped[Optional[str]] = mapped_column(types.String(32))
    priority: Mapped[Optional[str]] = mapped_column(types.Enum("diagnostic", "research"))
    project_account_ki: Mapped[Optional[str]] = mapped_column(types.String(32))
    project_account_kth: Mapped[Optional[str]] = mapped_column(types.String(32))
    return_samples: Mapped[bool] = mapped_column(types.Boolean, default=False)
    scout_access: Mapped[bool] = mapped_column(types.Boolean, default=False)
    uppmax_account: Mapped[Optional[str]] = mapped_column(types.String(32))
    data_archive_location: Mapped[str] = mapped_column(
        types.String(32), default=PDC_ARCHIVE_LOCATION
    )
    is_clinical: Mapped[bool] = mapped_column(types.Boolean, default=False)

    collaborations: Mapped[list["Collaboration"]] = orm.relationship(
        secondary="customer_collaboration", back_populates="customers"
    )

    delivery_contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    delivery_contact: Mapped[Optional["User"]] = orm.relationship(
        foreign_keys=[delivery_contact_id]
    )
    invoice_contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    invoice_contact: Mapped[Optional["User"]] = orm.relationship(foreign_keys=[invoice_contact_id])
    primary_contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    primary_contact: Mapped[Optional["User"]] = orm.relationship(foreign_keys=[primary_contact_id])

    panels: Mapped[list["Panel"]] = orm.relationship(back_populates="customer")
    users: Mapped[list["User"]] = orm.relationship(
        secondary=customer_user, back_populates="customers"
    )

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    @property
    def collaborators(self) -> set["Customer"]:
        """All customers that the current customer collaborates with (including itself)"""
        customers = {
            customer
            for collaboration in self.collaborations
            for customer in collaboration.customers
        }
        customers.add(self)
        return customers

    def to_dict(self):
        return to_dict(model_instance=self)


class Collaboration(Base):
    __tablename__ = "collaboration"
    id: Mapped[int] = mapped_column(primary_key=True)
    internal_id: Mapped[str] = mapped_column(
        types.String(32),
        unique=True,
    )
    name: Mapped[str] = mapped_column(types.String(128))
    customers: Mapped[list["Customer"]] = orm.relationship(
        secondary="customer_collaboration", back_populates="collaborations"
    )

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    def to_dict(self):
        """Represent as dictionary"""
        return {
            "customers": [customer.internal_id for customer in self.customers],
            "id": self.id,
            "name": self.name,
            "internal_id": self.internal_id,
        }


class Delivery(Base):
    __tablename__ = "delivery"
    id: Mapped[int] = mapped_column(primary_key=True)
    delivered_at: Mapped[Optional[datetime]]
    removed_at: Mapped[Optional[datetime]]
    destination: Mapped[Optional[str]] = mapped_column(
        types.Enum("caesar", "pdc", "uppmax", "mh", "custom"), default="caesar"
    )
    sample_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sample.id", ondelete="CASCADE"))
    pool_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pool.id", ondelete="CASCADE"))
    comment: Mapped[Optional[str]] = mapped_column(types.Text)

    def to_dict(self):
        return to_dict(model_instance=self)


class Case(Base, PriorityMixin):
    __tablename__ = "case"
    __table_args__ = (UniqueConstraint("customer_id", "name", name="_customer_name_uc"),)

    action: Mapped[Optional[CaseActions]] = mapped_column(types.Enum(*CaseActions.actions()))
    _cohorts: Mapped[Optional[str]] = mapped_column(types.Text)
    comment: Mapped[Optional[str]] = mapped_column(types.Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(types.DateTime, default=datetime.now)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"))
    customer: Mapped["Customer"] = orm.relationship(foreign_keys=[customer_id])
    data_analysis: Mapped[Optional[Workflow]] = mapped_column(types.Enum(*list(Workflow)))
    data_delivery: Mapped[Optional[DataDelivery]] = mapped_column(types.Enum(*list(DataDelivery)))
    id: Mapped[int] = mapped_column(primary_key=True)
    internal_id: Mapped[str] = mapped_column(types.String(32), unique=True)
    is_compressible: Mapped[bool] = mapped_column(default=True)
    name: Mapped[str] = mapped_column(types.String(128))
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("order.id"))
    ordered_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    _panels: Mapped[Optional[str]] = mapped_column(types.Text)

    priority: Mapped[Priority] = mapped_column(
        default=Priority.standard,
    )
    synopsis: Mapped[Optional[str]] = mapped_column(types.Text)
    tickets: Mapped[Optional[str]] = mapped_column(types.VARCHAR(128))

    analyses: Mapped[list["Analysis"]] = orm.relationship(
        back_populates="case", order_by="-Analysis.completed_at"
    )
    links: Mapped[list["CaseSample"]] = orm.relationship(back_populates="case")

    @property
    def cohorts(self) -> list[str]:
        """Return a list of cohorts."""
        return self._cohorts.split(",") if self._cohorts else []

    @cohorts.setter
    def cohorts(self, cohort_list: list[str]):
        self._cohorts = ",".join(cohort_list) if cohort_list else None

    @property
    def panels(self) -> list[str]:
        """Return a list of panels."""
        return self._panels.split(",") if self._panels else []

    @panels.setter
    def panels(self, panel_list: list[str]):
        self._panels = ",".join(panel_list) if panel_list else None

    @property
    def latest_ticket(self) -> str | None:
        """Returns the last ticket the family was ordered in"""
        return self.tickets.split(sep=",")[-1] if self.tickets else None

    @property
    def latest_analyzed(self) -> datetime | None:
        return self.analyses[0].completed_at if self.analyses else None

    @property
    def latest_sequenced(self) -> datetime | None:
        sequenced_dates = []
        for link in self.links:
            if link.sample.application_version.application.is_external:
                sequenced_dates.append(link.sample.ordered_at)
            elif link.sample.last_sequenced_at:
                sequenced_dates.append(link.sample.last_sequenced_at)
        return max(sequenced_dates, default=None)

    @property
    def all_samples_pass_qc(self) -> bool:
        pass_qc = []
        for link in self.links:
            if link.sample.application_version.application.is_external or link.sample.sequencing_qc:
                pass_qc.append(True)
            else:
                pass_qc.append(False)
        return all(pass_qc)

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    @property
    def samples(self) -> list["Sample"]:
        """Return case samples."""
        return self._get_samples

    @property
    def _get_samples(self) -> list["Sample"]:
        """Extract samples from a case."""
        return [link.sample for link in self.links]

    @property
    def tumour_samples(self) -> list["Sample"]:
        """Return tumour samples."""
        return self._get_tumour_samples

    @property
    def _get_tumour_samples(self) -> list["Sample"]:
        """Extract tumour samples."""
        return [link.sample for link in self.links if link.sample.is_tumour]

    @property
    def loqusdb_uploaded_samples(self) -> list["Sample"]:
        """Return uploaded samples to Loqusdb."""
        return self._get_loqusdb_uploaded_samples

    @property
    def _get_loqusdb_uploaded_samples(self) -> list["Sample"]:
        """Extract samples uploaded to Loqusdb."""
        return [link.sample for link in self.links if link.sample.loqusdb_id]

    @property
    def is_uploaded(self) -> bool:
        """Returns True if the latest connected analysis has been uploaded."""
        return self.analyses and self.analyses[0].uploaded_at

    @property
    def slurm_priority(self) -> SlurmQos:
        case_priority: str = self.priority
        slurm_priority: str = Priority.priority_to_slurm_qos().get(case_priority)
        return SlurmQos(slurm_priority)

    def get_delivery_arguments(self) -> set[str]:
        """Translates the case data_delivery field to workflow specific arguments."""
        delivery_arguments: set[str] = set()
        requested_deliveries: list[str] = re.split("[-_]", self.data_delivery)
        delivery_per_workflow_map: dict[str, str] = {
            DataDelivery.FASTQ: Workflow.FASTQ,
            DataDelivery.ANALYSIS_FILES: self.data_analysis,
        }
        for data_delivery, workflow in delivery_per_workflow_map.items():
            if data_delivery in requested_deliveries:
                delivery_arguments.add(workflow)
        return delivery_arguments

    def to_dict(self, links: bool = False, analyses: bool = False) -> dict:
        """Represent as dictionary."""
        data = to_dict(model_instance=self)
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


class CaseSample(Base):
    __tablename__ = "case_sample"
    __table_args__ = (UniqueConstraint("case_id", "sample_id", name="_case_sample_uc"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("case.id", ondelete="CASCADE"))
    sample_id: Mapped[int] = mapped_column(ForeignKey("sample.id", ondelete="CASCADE"))
    status: Mapped[StatusOptions] = mapped_column(default=SexOptions.UNKNOWN)

    created_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=datetime.now)

    mother_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sample.id"))
    father_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sample.id"))

    case: Mapped["Case"] = orm.relationship(back_populates="links")
    sample: Mapped["Sample"] = orm.relationship(foreign_keys=[sample_id], back_populates="links")
    mother: Mapped[Optional["Sample"]] = orm.relationship(
        foreign_keys=[mother_id], back_populates="mother_links"
    )
    father: Mapped[Optional["Sample"]] = orm.relationship(
        foreign_keys=[father_id], back_populates="father_links"
    )

    def to_dict(self, parents: bool = False, samples: bool = False, family: bool = False) -> dict:
        """Represent as dictionary"""
        data = to_dict(model_instance=self)
        if samples:
            data["sample"] = self.sample.to_dict()
            data["mother"] = self.mother.to_dict() if self.mother else None
            data["father"] = self.father.to_dict() if self.father else None
        elif parents:
            data["mother"] = self.mother.to_dict() if self.mother else None
            data["father"] = self.father.to_dict() if self.father else None
        if family:
            data["family"] = self.case.to_dict()
        return data

    def __str__(self) -> str:
        return f"{self.case.internal_id} | {self.sample.internal_id}"


class Flowcell(Base):
    __tablename__ = "flowcell"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(types.String(32), unique=True)
    sequencer_type: Mapped[Optional[str]] = mapped_column(
        types.Enum("hiseqga", "hiseqx", "novaseq", "novaseqx")
    )
    sequencer_name: Mapped[Optional[str]] = mapped_column(types.String(32))
    sequenced_at: Mapped[Optional[datetime]]
    status: Mapped[Optional[FlowCellStatus]] = mapped_column(default="ondisk")
    archived_at: Mapped[Optional[datetime]]
    has_backup: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=datetime.now)

    samples: Mapped[list["Sample"]] = orm.relationship(
        secondary=flowcell_sample, back_populates="flowcells"
    )
    sequencing_metrics: Mapped[list["SampleLaneSequencingMetrics"]] = orm.relationship(
        back_populates="flowcell",
        cascade="all, delete, delete-orphan",
    )

    def __str__(self):
        return self.name

    def to_dict(self, samples: bool = False):
        """Represent as dictionary"""
        data = to_dict(model_instance=Flowcell)
        if samples:
            data["samples"] = [sample.to_dict() for sample in self.samples]
        return data


class Organism(Base):
    __tablename__ = "organism"
    id: Mapped[int] = mapped_column(primary_key=True)
    internal_id: Mapped[str] = mapped_column(types.String(32), unique=True)
    name: Mapped[str] = mapped_column(types.String(255), unique=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=datetime.now)
    reference_genome: Mapped[Optional[str]] = mapped_column(types.String(255))
    verified: Mapped[Optional[bool]] = mapped_column(default=False)
    comment: Mapped[Optional[str]] = mapped_column(types.Text)

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    def to_dict(self) -> dict:
        """Represent as dictionary"""
        return to_dict(model_instance=self)


class Panel(Base):
    __tablename__ = "panel"
    abbrev: Mapped[Optional[str]] = mapped_column(types.String(32), unique=True)
    current_version: Mapped[float]
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"))
    customer: Mapped["Customer"] = orm.relationship(back_populates="panels")
    date: Mapped[datetime]
    gene_count: Mapped[Optional[int]]
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(types.String(64), unique=True)

    def __str__(self):
        return f"{self.abbrev} ({self.current_version})"

    def to_dict(self):
        return to_dict(model_instance=self)


class Pool(Base):
    __tablename__ = "pool"
    __table_args__ = (UniqueConstraint("order", "name", name="_order_name_uc"),)

    application_version_id: Mapped[int] = mapped_column(ForeignKey("application_version.id"))
    application_version: Mapped["ApplicationVersion"] = orm.relationship(
        foreign_keys=[application_version_id]
    )
    comment: Mapped[Optional[str]] = mapped_column(types.Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"))
    customer: Mapped["Customer"] = orm.relationship(foreign_keys=[customer_id])
    delivered_at: Mapped[Optional[datetime]]
    deliveries: Mapped[list["Delivery"]] = orm.relationship(backref="pool")
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[Optional[int]] = mapped_column(ForeignKey("invoice.id"))
    name: Mapped[str] = mapped_column(types.String(32))
    no_invoice: Mapped[Optional[bool]] = mapped_column(default=False)
    order: Mapped[str] = mapped_column(types.String(64))
    ordered_at: Mapped[datetime]
    received_at: Mapped[Optional[datetime]]
    ticket: Mapped[Optional[str]] = mapped_column(types.String(32))

    invoice: Mapped[Optional["Invoice"]] = orm.relationship(back_populates="pools")

    def to_dict(self):
        return to_dict(model_instance=self)


class Sample(Base, PriorityMixin):
    __tablename__ = "sample"
    age_at_sampling: Mapped[Optional[float]]
    application_version_id: Mapped[int] = mapped_column(ForeignKey("application_version.id"))
    application_version: Mapped["ApplicationVersion"] = orm.relationship(
        foreign_keys=[application_version_id]
    )
    capture_kit: Mapped[Optional[str]] = mapped_column(types.String(64))
    comment: Mapped[Optional[str]] = mapped_column(types.Text)
    control: Mapped[Optional[ControlOptions]]
    created_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"))
    customer: Mapped["Customer"] = orm.relationship(foreign_keys=[customer_id])
    delivered_at: Mapped[Optional[datetime]]
    deliveries: Mapped[list["Delivery"]] = orm.relationship(backref="sample")
    downsampled_to: Mapped[Optional[int]] = mapped_column(types.BigInteger)
    from_sample: Mapped[Optional[str]] = mapped_column(types.String(128))
    id: Mapped[int] = mapped_column(primary_key=True)
    internal_id: Mapped[str] = mapped_column(types.String(32), unique=True)
    invoice_id: Mapped[Optional[int]] = mapped_column(ForeignKey("invoice.id"))
    invoiced_at: Mapped[Optional[datetime]]  # DEPRECATED
    _is_external: Mapped[Optional[bool]] = mapped_column("is_external")  # DEPRECATED
    is_tumour: Mapped[Optional[bool]] = mapped_column(default=False)
    loqusdb_id: Mapped[Optional[str]] = mapped_column(types.String(64))
    name: Mapped[str] = mapped_column(types.String(128))
    no_invoice: Mapped[bool] = mapped_column(default=False)
    order: Mapped[Optional[str]] = mapped_column(types.String(64))
    ordered_at: Mapped[datetime]
    organism_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organism.id"))
    organism: Mapped[Optional["Organism"]] = orm.relationship(foreign_keys=[organism_id])
    original_ticket: Mapped[Optional[str]] = mapped_column(types.String(32))
    _phenotype_groups: Mapped[Optional[str]] = mapped_column(types.Text)
    _phenotype_terms: Mapped[Optional[str]] = mapped_column(types.Text)
    prepared_at: Mapped[Optional[datetime]]

    priority: Mapped[Priority] = mapped_column(default=Priority.standard)
    reads: Mapped[Optional[int]] = mapped_column(types.BigInteger, default=0)
    last_sequenced_at: Mapped[Optional[datetime]]
    received_at: Mapped[Optional[datetime]]
    reference_genome: Mapped[Optional[str]] = mapped_column(types.String(255))
    sequence_start: Mapped[Optional[datetime]]
    sex: Mapped[SexOptions]
    subject_id: Mapped[Optional[str]] = mapped_column(types.String(128))

    links: Mapped[list["CaseSample"]] = orm.relationship(
        foreign_keys=[CaseSample.sample_id], back_populates="sample"
    )
    mother_links: Mapped[list["CaseSample"]] = orm.relationship(
        foreign_keys=[CaseSample.mother_id], back_populates="mother"
    )
    father_links: Mapped[list["CaseSample"]] = orm.relationship(
        foreign_keys=[CaseSample.father_id], back_populates="father"
    )
    flowcells: Mapped[list["Flowcell"]] = orm.relationship(
        secondary=flowcell_sample, back_populates="samples"
    )
    sequencing_metrics: Mapped[list["SampleLaneSequencingMetrics"]] = orm.relationship(
        back_populates="sample"
    )
    invoice: Mapped[Optional["Invoice"]] = orm.relationship(back_populates="samples")

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"

    @property
    @deprecated(
        version="1.4.0",
        message="This field is deprecated, use sample.application_version.application.is_external",
    )
    def is_external(self):
        """Return if this is an externally sequenced sample."""
        return self._is_external

    @property
    def sequencing_qc(self) -> bool:
        """Return sequencing qc passed or failed."""
        application = self.application_version.application
        # Express priority needs to be analyzed at a lower threshold for primary analysis
        if self.priority == Priority.express:
            one_half_of_target_reads = application.target_reads / 2
            return self.reads >= one_half_of_target_reads
        if self.application_version.application.prep_category == PrepCategory.READY_MADE_LIBRARY:
            return bool(self.reads)
        return self.reads > application.expected_reads

    @property
    def phenotype_groups(self) -> list[str]:
        """Return a list of phenotype_groups."""
        return self._phenotype_groups.split(",") if self._phenotype_groups else []

    @phenotype_groups.setter
    def phenotype_groups(self, phenotype_term_list: list[str]):
        self._phenotype_groups = ",".join(phenotype_term_list) if phenotype_term_list else None

    @property
    def phenotype_terms(self) -> list[str]:
        """Return a list of phenotype_terms."""
        return self._phenotype_terms.split(",") if self._phenotype_terms else []

    @phenotype_terms.setter
    def phenotype_terms(self, phenotype_term_list: list[str]):
        self._phenotype_terms = ",".join(phenotype_term_list) if phenotype_term_list else None

    @property
    def prep_category(self) -> str:
        """Return the preparation category of the sample."""
        return self.application_version.application.prep_category

    @property
    def state(self) -> str:
        """Get the current sample state."""
        if self.delivered_at:
            return f"Delivered {self.delivered_at.date()}"
        if self.last_sequenced_at:
            return f"Sequenced {self.last_sequenced_at.date()}"
        if self.sequence_start:
            return f"Sequencing {self.sequence_start.date()}"
        if self.received_at:
            return f"Received {self.received_at.date()}"

        return f"Ordered {self.ordered_at.date()}"

    @property
    def archive_location(self) -> str:
        """Returns the data_archive_location if the customer linked to the sample."""
        return self.customer.data_archive_location

    @property
    def has_reads(self) -> bool:
        return bool(self.reads)

    def to_dict(self, links: bool = False, flowcells: bool = False) -> dict:
        """Represent as dictionary"""
        data = to_dict(model_instance=self)
        data["priority"] = self.priority_human
        data["customer"] = self.customer.to_dict()
        data["application_version"] = self.application_version.to_dict()
        data["application"] = self.application_version.application.to_dict()
        if links:
            data["links"] = [link_obj.to_dict(family=True, parents=True) for link_obj in self.links]
        if flowcells:
            data["flowcells"] = [flowcell_obj.to_dict() for flowcell_obj in self.flowcells]
        return data


class Invoice(Base):
    __tablename__ = "invoice"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id"))
    customer: Mapped["Customer"] = orm.relationship(foreign_keys=[customer_id])
    created_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=datetime.now)
    invoiced_at: Mapped[Optional[datetime]]
    comment: Mapped[Optional[str]] = mapped_column(types.Text)
    discount: Mapped[Optional[int]] = mapped_column(default=0)
    excel_kth: Mapped[Optional[Any]] = mapped_column(types.BLOB)
    excel_ki: Mapped[Optional[Any]] = mapped_column(types.BLOB)
    price: Mapped[Optional[int]]
    record_type: Mapped[Optional[str]] = mapped_column(types.Text)

    samples: Mapped[list["Sample"]] = orm.relationship(back_populates="invoice")
    pools: Mapped[list["Pool"]] = orm.relationship(back_populates="invoice")

    def __str__(self):
        return f"{self.customer_id} ({self.invoiced_at})"

    def to_dict(self) -> dict:
        """Represent as dictionary"""
        return to_dict(model_instance=self)


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(types.String(128))
    email: Mapped[str] = mapped_column(types.String(128), unique=True)
    is_admin: Mapped[Optional[bool]] = mapped_column(default=False)
    order_portal_login: Mapped[Optional[bool]] = mapped_column(default=False)

    customers: Mapped[list["Customer"]] = orm.relationship(
        secondary=customer_user, back_populates="users"
    )

    def to_dict(self) -> dict:
        """Represent as dictionary."""
        dict_representation: dict = to_dict(model_instance=self)
        dict_representation["customers"] = [customer.to_dict() for customer in self.customers]
        return dict_representation

    def __str__(self) -> str:
        return self.name


class SampleLaneSequencingMetrics(Base):
    """Model for storing sequencing metrics per lane and sample."""

    __tablename__ = "sample_lane_sequencing_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    flow_cell_name: Mapped[str] = mapped_column(types.String(32), ForeignKey("flowcell.name"))
    flow_cell_lane_number: Mapped[Optional[int]]

    sample_internal_id: Mapped[int] = mapped_column(
        types.String(32), ForeignKey("sample.internal_id")
    )
    sample_total_reads_in_lane: Mapped[Optional[int]] = mapped_column(types.BigInteger)
    sample_base_percentage_passing_q30: Mapped[Optional[float]] = mapped_column(types.Numeric(6, 2))
    sample_base_mean_quality_score: Mapped[Optional[float]] = mapped_column(types.Numeric(6, 2))

    created_at: Mapped[Optional[datetime]]

    flowcell: Mapped["Flowcell"] = orm.relationship(back_populates="sequencing_metrics")
    sample: Mapped["Sample"] = orm.relationship(back_populates="sequencing_metrics")

    __table_args__ = (
        UniqueConstraint(
            "flow_cell_name",
            "sample_internal_id",
            "flow_cell_lane_number",
            name="uix_flowcell_sample_lane",
        ),
    )

    def to_dict(self):
        return to_dict(model_instance=self)


class Order(Base):
    """Model for storing orders."""

    __tablename__ = "order"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id"))
    customer: Mapped["Customer"] = orm.relationship(foreign_keys=[customer_id])
    order_date: Mapped[datetime] = mapped_column(default=datetime.now())
    ticket_id: Mapped[int] = mapped_column(unique=True, index=True)
    workflow: Mapped[Workflow]

    def to_dict(self):
        return to_dict(model_instance=self)

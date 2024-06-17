import logging
from datetime import datetime

import petname
from sqlalchemy import Insert
from sqlalchemy.orm import Session

from cg.constants import DataDelivery, FlowCellStatus, Priority, Workflow
from cg.constants.archiving import PDC_ARCHIVE_LOCATION
from cg.models.orders.order import OrderIn
from cg.services.illumina_services.illumina_metrics_service.models import (
    IlluminaFlowCellDTO,
    IlluminaSampleSequencingMetricsDTO,
    IlluminaSequencingRunDTO,
)
from cg.store.base import BaseHandler
from cg.store.database import get_session
from cg.store.models import (
    Analysis,
    Application,
    ApplicationLimitations,
    ApplicationVersion,
    Bed,
    BedVersion,
    Case,
    CaseSample,
    Collaboration,
    Customer,
    Flowcell,
    IlluminaFlowCell,
    IlluminaSampleSequencingMetrics,
    IlluminaSequencingRun,
    Invoice,
    Order,
    Organism,
    Panel,
    Pool,
    Sample,
    SampleLaneSequencingMetrics,
    User,
    order_case,
)

LOG = logging.getLogger(__name__)


class CreateHandler(BaseHandler):
    """Methods related to adding new data to the store."""

    def generate_readable_sample_id(self) -> str:
        """Generates a petname as sample internal id for development purposes. Not used in normal production flow."""
        while True:
            random_id: str = petname.Generate(3, separator="")
            if not self.get_sample_by_internal_id(random_id):
                return random_id

    def generate_readable_case_id(self) -> str:
        while True:
            random_id: str = petname.Generate(2, separator="", letters=10)
            if not self.get_case_by_internal_id(random_id):
                return random_id

    def add_customer(
        self,
        internal_id: str,
        name: str,
        invoice_address: str,
        invoice_reference: str,
        data_archive_location: str = PDC_ARCHIVE_LOCATION,
        scout_access: bool = False,
        is_clinical: bool = False,
        *args,
        **kwargs,
    ) -> Customer:
        """Build a new customer record."""

        return Customer(
            internal_id=internal_id,
            name=name,
            scout_access=scout_access,
            invoice_address=invoice_address,
            invoice_reference=invoice_reference,
            data_archive_location=data_archive_location,
            is_clinical=is_clinical,
            **kwargs,
        )

    def add_collaboration(self, internal_id: str, name: str, **kwargs) -> Collaboration:
        """Build a new customer group record."""

        return Collaboration(internal_id=internal_id, name=name, **kwargs)

    def add_user(self, customer: Customer, email: str, name: str, is_admin: bool = False) -> User:
        """Build a new user record."""

        new_user = User(name=name, email=email, is_admin=is_admin)
        new_user.customers.append(customer)
        return new_user

    def add_application(
        self,
        tag: str,
        prep_category: str,
        description: str,
        percent_kth: int,
        percent_reads_guaranteed: int,
        is_accredited: bool = False,
        min_sequencing_depth: int = 0,
        **kwargs,
    ) -> Application:
        """Build a new application record."""

        return Application(
            tag=tag,
            prep_category=prep_category,
            description=description,
            is_accredited=is_accredited,
            min_sequencing_depth=min_sequencing_depth,
            percent_kth=percent_kth,
            percent_reads_guaranteed=percent_reads_guaranteed,
            **kwargs,
        )

    def add_application_version(
        self,
        application: Application,
        version: int,
        valid_from: datetime,
        prices: dict,
        **kwargs,
    ) -> ApplicationVersion:
        """Build a new application version record."""

        new_record = ApplicationVersion(version=version, valid_from=valid_from, **kwargs)
        for price_key in [
            Priority.standard.name,
            Priority.priority.name,
            Priority.express.name,
            Priority.research.name,
        ]:
            setattr(new_record, f"price_{price_key}", prices[price_key])
        new_record.application = application
        return new_record

    @staticmethod
    def add_application_limitation(
        application: Application,
        workflow: str,
        limitations: str,
        comment: str = "Dummy comment",
        created_at: datetime = datetime.now(),
        updated_at: datetime = datetime.now(),
        **kwargs,
    ) -> ApplicationLimitations:
        """Build a new application limitations record."""
        return ApplicationLimitations(
            application=application,
            workflow=workflow,
            limitations=limitations,
            comment=comment,
            created_at=created_at,
            updated_at=updated_at,
            **kwargs,
        )

    def add_bed(self, name: str) -> Bed:
        """Build a new bed record."""
        return Bed(name=name)

    def add_bed_version(self, bed: Bed, version: int, filename: str, shortname: str) -> BedVersion:
        """Build a new bed version record."""
        bed_version: BedVersion = BedVersion(
            version=version, filename=filename, shortname=shortname
        )
        bed_version.bed = bed
        return bed_version

    def add_sample(
        self,
        name: str,
        sex: str,
        comment: str = None,
        control: str = None,
        downsampled_to: int = None,
        internal_id: str = None,
        last_sequenced_at: datetime = None,
        order: str = None,
        ordered: datetime = None,
        prepared_at: datetime = None,
        priority: Priority = None,
        received: datetime = None,
        original_ticket: str = None,
        tumour: bool = False,
        **kwargs,
    ) -> Sample:
        """Build a new Sample record."""

        internal_id = internal_id or self.generate_readable_sample_id()
        priority = priority or (Priority.research if downsampled_to else Priority.standard)
        return Sample(
            comment=comment,
            control=control,
            downsampled_to=downsampled_to,
            internal_id=internal_id,
            is_tumour=tumour,
            last_sequenced_at=last_sequenced_at,
            name=name,
            order=order,
            ordered_at=ordered or datetime.now(),
            original_ticket=original_ticket,
            prepared_at=prepared_at,
            priority=priority,
            received_at=received,
            sex=sex,
            **kwargs,
        )

    def add_case(
        self,
        data_analysis: Workflow,
        data_delivery: DataDelivery,
        name: str,
        ticket: str,
        panels: list[str] | None = None,
        cohorts: list[str] | None = None,
        priority: Priority | None = Priority.standard,
        synopsis: str | None = None,
        customer_id: int | None = None,
    ) -> Case:
        """Build a new Case record."""

        internal_id: str = self.generate_readable_case_id()
        return Case(
            cohorts=cohorts,
            data_analysis=str(data_analysis),
            data_delivery=str(data_delivery),
            internal_id=internal_id,
            name=name,
            panels=panels,
            priority=priority,
            synopsis=synopsis,
            tickets=ticket,
            customer_id=customer_id,
        )

    def relate_sample(
        self,
        case: Case,
        sample: Sample,
        status: str,
        mother: Sample = None,
        father: Sample = None,
    ) -> CaseSample:
        """Relate a sample record to a family record."""

        new_record: CaseSample = CaseSample(status=status)
        new_record.case = case
        new_record.sample = sample
        new_record.mother = mother
        new_record.father = father
        return new_record

    def add_flow_cell(
        self,
        flow_cell_name: str,
        sequencer_name: str,
        sequencer_type: str,
        date: datetime,
        flow_cell_status: str | None = FlowCellStatus.ON_DISK,
        has_backup: bool | None = False,
    ) -> Flowcell:
        """Build a new Flowcell record."""
        return Flowcell(
            name=flow_cell_name,
            sequencer_name=sequencer_name,
            sequencer_type=sequencer_type,
            sequenced_at=date,
            status=flow_cell_status,
            has_backup=has_backup,
        )

    def add_analysis(
        self,
        workflow: Workflow,
        version: str = None,
        completed_at: datetime = None,
        primary: bool = False,
        uploaded: datetime = None,
        started_at: datetime = None,
        **kwargs,
    ) -> Analysis:
        """Build a new Analysis record."""
        return Analysis(
            workflow=workflow,
            workflow_version=version,
            completed_at=completed_at,
            is_primary=primary,
            uploaded_at=uploaded,
            started_at=started_at,
            **kwargs,
        )

    def add_panel(
        self,
        customer: Customer,
        name: str,
        abbrev: str,
        version: float,
        date: datetime = None,
        genes: int = None,
    ) -> Panel:
        """Build a new panel record."""

        new_record = Panel(
            name=name, abbrev=abbrev, current_version=version, date=date, gene_count=genes
        )
        new_record.customer = customer
        return new_record

    def add_pool(
        self,
        customer: Customer,
        name: str,
        order: str,
        ordered: datetime,
        application_version: ApplicationVersion,
        ticket: str = None,
        comment: str = None,
        received_at: datetime = None,
        invoice_id: int = None,
        no_invoice: bool = None,
        delivered_at: datetime = None,
    ) -> Pool:
        """Build a new Pool record."""

        new_record: Pool = Pool(
            name=name,
            ordered_at=ordered or datetime.now(),
            order=order,
            ticket=ticket,
            received_at=received_at,
            comment=comment,
            delivered_at=delivered_at,
            invoice_id=invoice_id,
            no_invoice=no_invoice,
        )
        new_record.customer = customer
        new_record.application_version = application_version
        return new_record

    def add_invoice(
        self,
        customer: Customer,
        samples: list[Sample] = None,
        microbial_samples: list[Sample] = None,
        pools: list[Pool] = None,
        comment: str = None,
        discount: int = 0,
        record_type: str = None,
        invoiced_at: datetime | None = None,
    ):
        """Build a new Invoice record."""

        new_id = self.new_invoice_id()
        new_invoice: Invoice = Invoice(
            comment=comment,
            discount=discount,
            id=new_id,
            record_type=record_type,
            invoiced_at=invoiced_at,
        )
        new_invoice.customer = customer
        for sample in samples or []:
            new_invoice.samples.append(sample)
        for microbial_sample in microbial_samples or []:
            new_invoice.samples.append(microbial_sample)
        for pool in pools or []:
            new_invoice.pools.append(pool)
        return new_invoice

    def add_organism(
        self,
        internal_id: str,
        name: str,
        reference_genome: str = None,
        verified: bool = False,
        **kwargs,
    ) -> Organism:
        """Build a new Organism record."""
        return Organism(
            internal_id=internal_id,
            name=name,
            reference_genome=reference_genome,
            verified=verified,
            **kwargs,
        )

    def add_sample_lane_sequencing_metrics(
        self, flow_cell_name: str, sample_internal_id: str, **kwargs
    ) -> SampleLaneSequencingMetrics:
        """Add a new SampleLaneSequencingMetrics record."""
        return SampleLaneSequencingMetrics(
            flow_cell_name=flow_cell_name,
            sample_internal_id=sample_internal_id,
            **kwargs,
        )

    def add_order(self, order_data: OrderIn):
        customer: Customer = self.get_customer_by_internal_id(order_data.customer)
        workflow: str = order_data.samples[0].data_analysis
        order = Order(
            customer_id=customer.id,
            ticket_id=order_data.ticket,
            workflow=workflow,
        )
        session: Session = get_session()
        session.add(order)
        session.commit()
        return order

    @staticmethod
    def link_case_to_order(order_id: int, case_id: int):
        insert_statement: Insert = order_case.insert().values(order_id=order_id, case_id=case_id)
        session: Session = get_session()
        session.execute(insert_statement)
        session.commit()

    def add_illumina_flow_cell(self, flow_cell_dto: IlluminaFlowCellDTO) -> IlluminaFlowCell:
        """Add a new Illumina flow cell to the status database as a pending transaction."""
        if self.get_illumina_flow_cell_by_internal_id(flow_cell_dto.internal_id):
            raise ValueError(f"Flow cell with {flow_cell_dto.internal_id} already exists.")
        new_flow_cell = IlluminaFlowCell(
            internal_id=flow_cell_dto.internal_id,
            type=flow_cell_dto.type,
            model=flow_cell_dto.model,
        )
        self.session.add(new_flow_cell)
        LOG.debug(f"Flow cell added to status db: {new_flow_cell.id}.")
        return new_flow_cell

    def add_illumina_sequencing_run(
        self, sequencing_run_dto: IlluminaSequencingRunDTO, flow_cell: IlluminaFlowCell
    ) -> IlluminaSequencingRun:
        """Add a new Illumina flow cell to the status database as a pending transaction."""
        new_sequencing_run = IlluminaSequencingRun(
            type=sequencing_run_dto.type,
            device=flow_cell,
            sequencer_type=sequencing_run_dto.sequencer_type,
            sequencer_name=sequencing_run_dto.sequencer_name,
            data_availability=sequencing_run_dto.data_availability,
            archived_at=sequencing_run_dto.archived_at,
            has_backup=sequencing_run_dto.has_backup,
            total_reads=sequencing_run_dto.total_reads,
            total_undetermined_reads=sequencing_run_dto.total_undetermined_reads,
            percent_undetermined_reads=sequencing_run_dto.percent_undetermined_reads,
            percent_q30=sequencing_run_dto.percent_q30,
            mean_quality_score=sequencing_run_dto.mean_quality_score,
            total_yield=sequencing_run_dto.total_yield,
            yield_q30=sequencing_run_dto.yield_q30,
            cycles=sequencing_run_dto.cycles,
            demultiplexing_software=sequencing_run_dto.demultiplexing_software,
            demultiplexing_software_version=sequencing_run_dto.demultiplexing_software_version,
            sequencing_started_at=sequencing_run_dto.sequencing_started_at,
            sequencing_completed_at=sequencing_run_dto.sequencing_completed_at,
            demultiplexing_started_at=sequencing_run_dto.demultiplexing_started_at,
            demultiplexing_completed_at=sequencing_run_dto.demultiplexing_completed_at,
        )
        self.session.add(new_sequencing_run)
        LOG.debug(f"Sequencing run added to status db: {new_sequencing_run.id}.")
        return new_sequencing_run

    def add_illumina_sample_metrics_entry(
        self, metrics_dto: IlluminaSampleSequencingMetricsDTO, sequencing_run: IlluminaSequencingRun
    ) -> IlluminaSampleSequencingMetrics:
        """
        Add a new Illumina Sample Sequencing Metrics entry to the status database as a pending
        transaction.
        """
        sample: Sample = self.get_sample_by_internal_id(metrics_dto.sample_id)
        new_metric = IlluminaSampleSequencingMetrics(
            sample=sample,
            instrument_run=sequencing_run,
            type=metrics_dto.type,
            flow_cell_lane=metrics_dto.flow_cell_lane,
            total_reads_in_lane=metrics_dto.total_reads_in_lane,
            base_passing_q30_percent=metrics_dto.base_passing_q30_percent,
            base_mean_quality_score=metrics_dto.base_mean_quality_score,
            yield_=metrics_dto.yield_,
            yield_q30=metrics_dto.yield_q30,
            created_at=metrics_dto.created_at,
        )
        self.session.add(new_metric)
        return new_metric

"""Utility functions to simply add test data in a cg store."""

import logging
from datetime import datetime
from pathlib import Path

from housekeeper.store.models import Bundle, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery, SequencingRunDataAvailability, Workflow
from cg.constants.devices import DeviceType
from cg.constants.pedigree import Pedigree
from cg.constants.priority import PriorityTerms
from cg.constants.sequencing import Sequencers
from cg.constants.subject import PhenotypeStatus, Sex
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.data_transfer.models import (
    IlluminaFlowCellDTO,
    IlluminaSampleSequencingMetricsDTO,
    IlluminaSequencingRunDTO,
)
from cg.store.exc import EntryNotFoundError
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
    IlluminaFlowCell,
    IlluminaSampleSequencingMetrics,
    IlluminaSequencingRun,
    Invoice,
    Order,
    OrderTypeApplication,
    Organism,
    Panel,
    Pool,
    Sample,
    User,
)
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class StoreHelpers:
    """Class to hold helper functions that needs to be used all over."""

    @staticmethod
    def ensure_hk_bundle(store: HousekeeperAPI, bundle_data: dict, include: bool = False) -> Bundle:
        """Utility function to add a bundle of information to a housekeeper api."""

        bundle_exists = False
        for bundle in store.bundles():
            if bundle.name != bundle_data["name"]:
                continue
            bundle_exists = True
            _bundle = bundle
            break

        if not bundle_exists:
            _bundle, _version = store.add_bundle(bundle_data)
            store.add_commit(_bundle)
            store.add_commit(_version)

        if include:
            store.include(_version)

        return _bundle

    @staticmethod
    def format_hk_bundle_dict(
        bundle_name: str, files: list[Path], all_tags: list[list[str]]
    ) -> dict:
        """Creates the dict representation for a housekeeper bundle with necessary values set."""
        return {
            "name": bundle_name,
            "created_at": datetime.now(),
            "expires_at": datetime.now(),
            "files": [
                {
                    "path": file.as_posix(),
                    "tags": tags,
                    "archive": False,
                }
                for file, tags in zip(files, all_tags)
            ],
        }

    @staticmethod
    def quick_hk_bundle(
        bundle_name: str, files: list[Path], store: HousekeeperAPI, tags: list[list[str]]
    ):
        """Adds a bundle to housekeeper with the given files and tags. Returns the new bundle.

        Arguments:
            bundle_name = The name of the bundle to be created.
            files = A list of files to be added to the bundle.
            store = The database instance where the bundle should be added.
            tags = A list where each entry is the set of tags for the corresponding file.
                   The length of this list should be the same as the length of the files list.
        """
        bundle_data: dict = StoreHelpers.format_hk_bundle_dict(
            bundle_name=bundle_name, files=files, all_tags=tags
        )
        return StoreHelpers.ensure_hk_bundle(store=store, bundle_data=bundle_data)

    @staticmethod
    def ensure_hk_version(store: HousekeeperAPI, bundle_data: dict) -> Version:
        """Utility function to return existing or create an version for tests."""
        _bundle = StoreHelpers.ensure_hk_bundle(store, bundle_data)
        return store.last_version(_bundle.name)

    @classmethod
    def ensure_application_version(
        cls,
        store: Store,
        application_tag: str = "dummy_tag",
        prep_category: str = "wgs",
        is_external: bool = False,
        is_rna: bool = False,
        description: str = None,
        sequencing_depth: int = None,
        is_accredited: bool = False,
        version: int = 1,
        valid_from: datetime = datetime.now(),
        **kwargs,
    ) -> ApplicationVersion:
        """Utility function to return existing or create application version for tests."""
        if is_rna:
            application_tag = "rna_tag"
            prep_category = "wts"

        application: Application = store.get_application_by_tag(tag=application_tag)
        if not application:
            application: Application = cls.add_application(
                store=store,
                application_tag=application_tag,
                prep_category=prep_category,
                is_external=is_external,
                description=description,
                is_accredited=is_accredited,
                sequencing_depth=sequencing_depth,
                **kwargs,
            )

        prices = {
            PriorityTerms.STANDARD: 10,
            PriorityTerms.PRIORITY: 20,
            PriorityTerms.EXPRESS: 30,
            PriorityTerms.RESEARCH: 5,
        }

        application_version: ApplicationVersion = StoreHelpers.add_application_version(
            store=store,
            application=application,
            prices=prices,
            version=version,
            valid_from=valid_from,
        )
        return application_version

    @staticmethod
    def add_application_version(
        store: Store,
        application: Application,
        prices: dict,
        version: int = 1,
        valid_from: datetime = datetime.now(),
    ) -> ApplicationVersion:
        """Add an application version to store."""
        new_record = (
            store._get_query(table=ApplicationVersion)
            .filter(ApplicationVersion.application_id == application.id)
            .first()
        )
        if not new_record:
            new_record: ApplicationVersion = store.add_application_version(
                application=application,
                version=version,
                valid_from=valid_from,
                prices=prices,
            )
        store.session.add(new_record)
        store.session.commit()
        return new_record

    @classmethod
    def ensure_application(
        cls,
        store: Store,
        tag: str,
        prep_category: str = "wgs",
        description: str = "dummy_description",
        is_archived: bool = False,
        **kwargs,
    ) -> Application:
        """Ensure that application exists in store."""
        application: Application = store.get_application_by_tag(tag=tag)
        if not application:
            application: Application = cls.add_application(
                store=store,
                application_tag=tag,
                prep_category=prep_category,
                description=description,
                is_archived=is_archived,
                **kwargs,
            )
        return application

    @staticmethod
    def add_application(
        store: Store,
        application_tag: str = "dummy_tag",
        prep_category: str = "wgs",
        description: str = None,
        is_archived: bool = False,
        target_reads: int = None,
        percent_reads_guaranteed: int = 75,
        is_accredited: bool = False,
        is_external: bool = False,
        min_sequencing_depth: int = 30,
        **kwargs,
    ) -> Application:
        """Utility function to add a application to a store."""
        application = store.get_application_by_tag(tag=application_tag)
        if application:
            return application

        if not description:
            description = "dummy_description"
        application = store.add_application(
            tag=application_tag,
            prep_category=prep_category,
            description=description,
            is_archived=is_archived,
            percent_kth=80,
            target_reads=target_reads,
            percent_reads_guaranteed=percent_reads_guaranteed,
            is_accredited=is_accredited,
            limitations="A limitation",
            is_external=is_external,
            min_sequencing_depth=min_sequencing_depth,
            **kwargs,
        )
        store.session.add(application)
        store.session.commit()
        return application

    def add_application_order_type(
        self, store: Store, application: Application, order_types: list[str]
    ):
        """Add an order type to an application."""
        order_app_links: list[OrderTypeApplication] = store.link_order_types_to_application(
            application=application, order_types=order_types
        )
        for link in order_app_links:
            store.session.add(link)
        store.session.commit()
        return order_app_links

    @staticmethod
    def ensure_application_limitation(
        store: Store,
        application: Application,
        workflow: str = Workflow.MIP_DNA,
        limitations: str = "Dummy limitations",
        **kwargs,
    ) -> ApplicationLimitations:
        """Ensure that application limitations exist in store."""
        application_limitation: ApplicationLimitations = (
            store.get_application_limitation_by_tag_and_workflow(
                tag=application.tag, workflow=workflow
            )
        )
        if application_limitation:
            return application_limitation
        application_limitation: ApplicationLimitations = store.add_application_limitation(
            application=application, workflow=workflow, limitations=limitations, **kwargs
        )
        store.session.add(application_limitation)
        store.session.commit()
        return application_limitation

    @staticmethod
    def ensure_bed_version(store: Store, bed_name: str = "dummy_bed") -> BedVersion:
        """Return existing or create and return bed version for tests."""
        bed: Bed | None = store.get_bed_by_name(bed_name)
        if not bed:
            bed: Bed = store.add_bed(name=bed_name)
            store.session.add(bed)

        bed_version: BedVersion = store.add_bed_version(
            bed=bed, version=1, filename="dummy_filename", shortname=bed_name
        )
        store.session.add(bed_version)
        store.session.commit()
        return bed_version

    @staticmethod
    def ensure_collaboration(store: Store, collaboration_id: str = "all_customers"):
        collaboration = store.get_collaboration_by_internal_id(collaboration_id)
        if not collaboration:
            collaboration = store.add_collaboration(collaboration_id, collaboration_id)
        return collaboration

    @classmethod
    def ensure_customer(
        cls,
        store: Store,
        customer_id: str = "cust000",
        customer_name: str = "Production",
        scout_access: bool = False,
    ) -> Customer:
        """Utility function to return existing or create customer for tests."""
        collaboration: Collaboration = cls.ensure_collaboration(store)
        customer: Customer = store.get_customer_by_internal_id(customer_internal_id=customer_id)

        if not customer:
            customer = store.add_customer(
                internal_id=customer_id,
                name=customer_name,
                scout_access=scout_access,
                invoice_address="Test street",
                invoice_reference="ABCDEF",
            )
            customer.collaborations.append(collaboration)
            store.session.add(customer)
            store.session.commit()
        return customer

    @staticmethod
    def add_analysis(
        store: Store,
        case: Case = None,
        started_at: datetime = None,
        completed_at: datetime = None,
        uploaded_at: datetime = None,
        upload_started: datetime = None,
        delivery_reported_at: datetime = None,
        cleaned_at: datetime = None,
        workflow: Workflow = Workflow.BALSAMIC,
        workflow_version: str = "1.0",
        data_delivery: DataDelivery = DataDelivery.FASTQ_QC,
        uploading: bool = False,
        config_path: str = None,
    ) -> Analysis:
        """Utility function to add an analysis for tests."""

        if not case:
            case = StoreHelpers.add_case(store, data_analysis=workflow, data_delivery=data_delivery)

        analysis = store.add_analysis(workflow=workflow, version=workflow_version, case_id=case.id)

        analysis.started_at = started_at or datetime.now()
        if completed_at:
            analysis.completed_at = completed_at
        if uploaded_at:
            analysis.uploaded_at = uploaded_at
        if delivery_reported_at:
            analysis.delivery_report_created_at = delivery_reported_at
        if cleaned_at:
            analysis.cleaned_at = cleaned_at
        if uploading:
            analysis.upload_started_at = upload_started or datetime.now()
        if config_path:
            analysis.config_path = config_path
        if workflow:
            analysis.workflow = str(workflow)

        analysis.limitations = "A limitation"
        analysis.case = case
        store.session.add(analysis)
        store.session.commit()
        return analysis

    @staticmethod
    def add_sample(
        store: Store,
        application_tag: str = "dummy_tag",
        application_type: str = "tgs",
        control: str = "",
        customer_id: str = None,
        sex: str = Sex.FEMALE,
        is_external: bool = False,
        is_rna: bool = False,
        is_tumour: bool = False,
        internal_id: str = None,
        reads: int = None,
        name: str = "sample_test",
        original_ticket: str = None,
        subject_id: str = None,
        **kwargs,
    ) -> Sample:
        """Utility function to add a sample to use in tests."""
        customer_id: str = customer_id or "cust000"
        customer: Customer = StoreHelpers.ensure_customer(store, customer_id=customer_id)
        application_version: ApplicationVersion = StoreHelpers.ensure_application_version(
            store=store,
            application_tag=application_tag,
            prep_category=application_type,
            is_external=is_external,
            is_rna=is_rna,
        )
        application_version_id: int = application_version.id

        if internal_id:
            if existing_sample := store.get_sample_by_internal_id(internal_id=internal_id):
                return existing_sample

        sample: Sample = store.add_sample(
            name=name,
            sex=sex,
            control=control,
            original_ticket=original_ticket,
            tumour=is_tumour,
            reads=reads,
            internal_id=internal_id,
            subject_id=subject_id,
        )

        sample.application_version_id = application_version_id
        sample.customer = customer
        sample.ordered_at = datetime.now()

        for key, value in kwargs.items():
            if hasattr(sample, key):
                setattr(sample, key, value)
            else:
                raise AttributeError(f"Unknown sample attribute/feature: {key}, {value}")

        store.session.add(sample)
        store.session.commit()
        return sample

    @staticmethod
    def ensure_panel(
        store: Store, panel_abbreviation: str = "panel_test", customer_id: str = "cust000"
    ) -> Panel:
        """Utility function to add a panel to use in tests."""
        customer = StoreHelpers.ensure_customer(store, customer_id)
        panel: Panel = store.get_panel_by_abbreviation(abbreviation=panel_abbreviation)
        if not panel:
            panel = store.add_panel(
                customer=customer,
                name=panel_abbreviation,
                abbrev=panel_abbreviation,
                version=1.0,
                date=datetime.now(),
                genes=1,
            )
            store.session.add(panel)
            store.session.commit()
        return panel

    @staticmethod
    def add_case(
        store: Store,
        name: str = "case_test",
        data_analysis: str = Workflow.MIP_DNA,
        data_delivery: DataDelivery = DataDelivery.SCOUT,
        action: str = None,
        internal_id: str = None,
        customer_id: str = "cust000",
        panels: list[str] = [],
        priority: str = PriorityTerms.STANDARD,
        case_obj: Case = None,
        ticket: str = "123456",
    ) -> Case:
        """Utility function to add a case to use in tests,
        If no case object is used a autogenerated case id will be used.

        """
        if not panels:
            panels: list[str] = ["panel_test"]
        customer = StoreHelpers.ensure_customer(store, customer_id=customer_id)
        if case_obj:
            panels = case_obj.panels
        for panel_abbreivation in panels:
            StoreHelpers.ensure_panel(
                store=store, panel_abbreviation=panel_abbreivation, customer_id=customer_id
            )

        if not case_obj:
            case_obj: Case | None = store.get_case_by_internal_id(internal_id=name)
        if not case_obj:
            case_obj = store.add_case(
                data_analysis=data_analysis,
                data_delivery=data_delivery,
                name=name,
                panels=panels,
                ticket=ticket,
                priority=priority,
            )
        if action:
            case_obj.action = action
        if internal_id:
            case_obj.internal_id = internal_id

        case_obj.customer = customer
        store.session.add(case_obj)
        store.session.commit()
        return case_obj

    @staticmethod
    def add_order(
        store: Store,
        customer_id: int,
        ticket_id: int,
        order_date: datetime = datetime(year=2023, month=12, day=24),
        workflow: Workflow = Workflow.MIP_DNA,
    ) -> Order:
        order = Order(
            customer_id=customer_id,
            ticket_id=ticket_id,
            order_date=order_date,
        )
        store.session.add(order)
        store.session.commit()
        return order

    @staticmethod
    def ensure_case(
        store: Store,
        case_name: str = "test-case",
        case_id: str = "blueeagle",
        customer: Customer = None,
        data_analysis: Workflow = Workflow.MIP_DNA,
        data_delivery: DataDelivery = DataDelivery.SCOUT,
        action: str = None,
        order: Order = None,
    ):
        """Load a case with samples and link relations."""
        if not customer:
            customer = StoreHelpers.ensure_customer(store=store)
        case = store.get_case_by_internal_id(
            internal_id=case_id
        ) or store.get_case_by_name_and_customer(customer=customer, case_name=case_name)
        if not case:
            case = StoreHelpers.add_case(
                store=store,
                data_analysis=data_analysis,
                data_delivery=data_delivery,
                name=case_name,
                internal_id=case_id,
                action=action,
            )
            case.customer = customer
        if order:
            store.link_case_to_order(order_id=order.id, case_id=case.id)
        return case

    @staticmethod
    def ensure_case_from_dict(
        store: Store,
        case_info: dict,
        app_tag: str = None,
        ordered_at: datetime = None,
        completed_at: datetime = None,
        created_at: datetime = datetime.now(),
        started_at: datetime = None,
    ):
        """Load a case with samples and link relations from a dictionary."""
        customer_obj = StoreHelpers.ensure_customer(store)
        order = store.get_order_by_ticket_id(ticket_id=int(case_info["tickets"])) or Order(
            ticket_id=int(case_info["tickets"]),
            customer_id=customer_obj.id,
        )
        case = Case(
            name=case_info["name"],
            panels=case_info["panels"],
            internal_id=case_info["internal_id"],
            ordered_at=ordered_at,
            data_analysis=case_info.get("data_analysis", Workflow.MIP_DNA),
            data_delivery=case_info.get("data_delivery", str(DataDelivery.SCOUT)),
            created_at=created_at,
            action=case_info.get("action"),
            tickets=case_info["tickets"],
        )
        case.orders.append(order)
        case = StoreHelpers.add_case(store, case_obj=case, customer_id=customer_obj.internal_id)

        app_tag = app_tag or "WGSPCFC030"
        app_type = case_info.get("application_type", "wgs")
        StoreHelpers.ensure_application_version(store, application_tag=app_tag)

        sample_objs = {}
        for sample_data in case_info["samples"]:
            sample_id = sample_data["internal_id"]
            sample_obj = StoreHelpers.add_sample(
                store,
                application_tag=app_tag,
                application_type=app_type,
                sex=sample_data["sex"],
                internal_id=sample_id,
                reads=sample_data["reads"],
                name=sample_data.get("name"),
                original_ticket=sample_data["original_ticket"],
                capture_kit=sample_data["capture_kit"],
            )
            sample_objs[sample_id] = sample_obj

            father = sample_objs.get(sample_data.get(Pedigree.FATHER))
            mother = sample_objs.get(sample_data.get(Pedigree.MOTHER))
            StoreHelpers.add_relationship(
                store,
                case=case,
                sample=sample_obj,
                status=sample_data.get("status", PhenotypeStatus.UNKNOWN),
                father=father,
                mother=mother,
            )

        StoreHelpers.add_analysis(
            store,
            case=case,
            started_at=started_at or datetime.now(),
            completed_at=completed_at or datetime.now(),
            workflow=Workflow.MIP_DNA,
        )
        return case

    @staticmethod
    def add_organism(
        store: Store,
        internal_id: str = "organism_test",
        name: str = "organism_name",
        reference_genome: str = "reference_genome_test",
    ) -> Organism:
        """Utility function to add an organism to use in tests."""
        return store.add_organism(
            internal_id=internal_id, name=name, reference_genome=reference_genome
        )

    @staticmethod
    def ensure_organism(
        store: Store,
        organism_id: str = "organism_test",
        name: str = "organism_name",
        reference_genome: str = "reference_genome_test",
    ) -> Organism:
        """Utility function to add an organism to use in tests."""
        organism = StoreHelpers.add_organism(
            store, internal_id=organism_id, name=name, reference_genome=reference_genome
        )
        store.session.add(organism)
        store.session.commit()
        return organism

    @staticmethod
    def add_microbial_sample(
        store: Store,
        sample_id: str = "microbial_sample_id",
        priority: str = PriorityTerms.RESEARCH,
        name: str = "microbial_name_test",
        organism: Organism = None,
        comment: str = "comment",
        ticket: int = 123456,
    ) -> Sample:
        """Utility function to add a sample to use in tests."""
        customer = StoreHelpers.ensure_customer(store, "cust_test")
        application_version = StoreHelpers.ensure_application_version(store)
        if not organism:
            organism = StoreHelpers.ensure_organism(store)

        sample = store.add_sample(
            name=name,
            comment=comment,
            internal_id=sample_id,
            priority=priority,
            application_version=application_version,
            organism=organism,
            reads=6000000,
            sex=Sex.UNKNOWN,
        )
        sample.customer = customer
        case = StoreHelpers.ensure_case(
            store=store,
            case_name=str(ticket),
            customer=customer,
            data_analysis=Workflow.MICROSALT,
            data_delivery=DataDelivery.FASTQ_QC,
        )
        StoreHelpers.add_relationship(store=store, case=case, sample=sample)
        return sample

    @staticmethod
    def add_samples(store: Store, nr_samples: int = 5) -> list[Sample]:
        """Utility function to add a number of samples to use in tests."""
        nr_samples = max(nr_samples, 2)
        return [
            StoreHelpers.add_sample(store, str(sample_id)) for sample_id in range(1, nr_samples)
        ]

    @staticmethod
    def add_illumina_flow_cell(
        store: Store, flow_cell_id: str = "flow_cell_test", model: str = "10B"
    ) -> IlluminaFlowCell:
        """Add an Illumina flow cell to the store and return it assuming it does not exist."""
        flow_cell_dto = IlluminaFlowCellDTO(
            internal_id=flow_cell_id, type=DeviceType.ILLUMINA, model=model
        )
        flow_cell: IlluminaFlowCell = store.add_illumina_flow_cell(flow_cell_dto)
        store.session.commit()
        return flow_cell

    @classmethod
    def ensure_illumina_flow_cell(
        cls,
        store: Store,
        flow_cell_id: str = "flow_cell_test",
        model: str = "10B",
    ) -> IlluminaFlowCell:
        """Return an Illumina flow cell if exists, otherwise add it to the store and return it."""
        try:
            flow_cell: IlluminaFlowCell | None = store.get_illumina_flow_cell_by_internal_id(
                internal_id=flow_cell_id
            )
        except EntryNotFoundError:
            flow_cell: IlluminaFlowCell = cls.add_illumina_flow_cell(
                store=store, flow_cell_id=flow_cell_id, model=model
            )
        return flow_cell

    @staticmethod
    def add_illumina_sequencing_run(
        store: Store,
        flow_cell: IlluminaFlowCell,
        timestamp_now: datetime = datetime.now(),
        sequencer_type: Sequencers = Sequencers.NOVASEQ,
        sequencer_name: str = "dummy_sequencer",
        data_availability: SequencingRunDataAvailability = SequencingRunDataAvailability.ON_DISK,
        archived_at: datetime = None,
        has_backup: bool | None = False,
    ) -> IlluminaSequencingRun:
        """Add an Illumina sequencing run to the store and return it assuming it does not exist."""
        illumina_run_dto = IlluminaSequencingRunDTO(
            type=DeviceType.ILLUMINA,
            sequencer_type=sequencer_type,
            sequencer_name=sequencer_name,
            data_availability=data_availability,
            archived_at=archived_at,
            has_backup=has_backup,
            total_reads=100_000_000,
            total_undetermined_reads=10,
            percent_undetermined_reads=0.1,
            percent_q30=90,
            mean_quality_score=35,
            total_yield=100,
            yield_q30=50,
            cycles=151,
            demultiplexing_software="dragen",
            demultiplexing_software_version="1.0.0",
            sequencing_started_at=timestamp_now,
            sequencing_completed_at=timestamp_now,
            demultiplexing_started_at=timestamp_now,
            demultiplexing_completed_at=timestamp_now,
        )
        illumina_run: IlluminaSequencingRun = store.add_illumina_sequencing_run(
            sequencing_run_dto=illumina_run_dto, flow_cell=flow_cell
        )
        store.session.commit()
        return illumina_run

    @classmethod
    def ensure_illumina_sequencing_run(
        cls,
        store: Store,
        flow_cell: IlluminaFlowCell,
        sequencer_type: Sequencers = Sequencers.NOVASEQ,
        sequencer_name: str = "dummy_sequencer",
        data_availability: SequencingRunDataAvailability = SequencingRunDataAvailability.ON_DISK,
        archived_at: datetime = None,
        has_backup: bool | None = False,
    ) -> IlluminaSequencingRun:
        """
        Return an Illumina sequencing run if exists, otherwise add it to the store and return it.
        """
        try:
            illumina_run: IlluminaSequencingRun | None = (
                store.get_illumina_sequencing_run_by_device_internal_id(
                    device_internal_id=flow_cell.internal_id
                )
            )
        except EntryNotFoundError:
            illumina_run: IlluminaSequencingRun = cls.add_illumina_sequencing_run(
                store=store,
                flow_cell=flow_cell,
                sequencer_type=sequencer_type,
                sequencer_name=sequencer_name,
                data_availability=data_availability,
                archived_at=archived_at,
                has_backup=has_backup,
            )
        return illumina_run

    @staticmethod
    def add_illumina_sample_sequencing_metrics_object(
        store: Store, sample_id: str, sequencing_run: IlluminaSequencingRun, lane: int
    ) -> IlluminaSampleSequencingMetrics:
        """
        Add an Illumina sample sequencing metrics object to the store given for a sample and lane,
        and return it assuming it does not exist.
        """

        metrics_dto = IlluminaSampleSequencingMetricsDTO(
            sample_id=sample_id,
            type=DeviceType.ILLUMINA,
            flow_cell_lane=lane,
            total_reads_in_lane=100,
            base_passing_q30_percent=90,
            base_mean_quality_score=35,
            yield_=100,
            yield_q30=0.9,
            created_at=datetime.now(),
        )
        metrics: IlluminaSampleSequencingMetrics = store.add_illumina_sample_metrics_entry(
            metrics_dto=metrics_dto, sequencing_run=sequencing_run
        )
        store.session.commit()
        return metrics

    @classmethod
    def ensure_illumina_sample_sequencing_metrics_object(
        cls,
        store: Store,
        sequencing_run: IlluminaSequencingRun,
        sample_id: str,
        lane: int,
    ) -> IlluminaSampleSequencingMetrics:
        """
        Return an Illumina sample sequencing metrics object if exists,
        otherwise add it to the store and return it.
        """
        illumina_sample_metrics: IlluminaSampleSequencingMetrics | None = (
            store.get_illumina_metrics_entry_by_device_sample_and_lane(
                device_internal_id=sequencing_run.device.internal_id,
                sample_internal_id=sample_id,
                lane=lane,
            )
        )
        if illumina_sample_metrics:
            return illumina_sample_metrics
        metrics: IlluminaSampleSequencingMetrics = (
            cls.add_illumina_sample_sequencing_metrics_object(
                store=store,
                sample_id=sample_id,
                sequencing_run=sequencing_run,
                lane=lane,
            )
        )
        return metrics

    @staticmethod
    def add_relationship(
        store: Store,
        sample: Sample,
        case: Case,
        status: str = PhenotypeStatus.UNKNOWN,
        father: Sample = None,
        mother: Sample = None,
    ) -> CaseSample:
        """Utility function to link a sample to a case."""
        link = store.relate_sample(
            sample=sample, case=case, status=status, father=father, mother=mother
        )
        store.session.add(link)
        store.session.commit()
        return link

    @staticmethod
    def add_synopsis_to_case(
        store: Store, case_id: str, synopsis: str = "a synopsis"
    ) -> Case | None:
        """Function for adding a synopsis to a case in the database."""
        case_obj: Case = store.get_case_by_internal_id(internal_id=case_id)
        if not case_obj:
            LOG.warning("Could not find case")
            return None
        case_obj.synopsis = synopsis
        store.session.commit()
        return case_obj

    @staticmethod
    def add_phenotype_groups_to_sample(
        store: Store, sample_id: str, phenotype_groups: [str] = None
    ) -> Sample | None:
        """Function for adding a phenotype group to a sample in the database."""
        if phenotype_groups is None:
            phenotype_groups = ["a phenotype group"]
        sample_obj: Sample = store.get_sample_by_internal_id(internal_id=sample_id)
        if not sample_obj:
            LOG.warning("Could not find sample")
            return None
        sample_obj.phenotype_groups = phenotype_groups
        store.session.commit()
        return sample_obj

    @staticmethod
    def add_phenotype_terms_to_sample(
        store: Store, sample_id: str, phenotype_terms: list[str] = []
    ) -> Sample | None:
        """Function for adding a phenotype term to a sample in the database."""
        if not phenotype_terms:
            phenotype_terms: list[str] = ["a phenotype term"]
        sample_obj: Sample = store.get_sample_by_internal_id(internal_id=sample_id)
        if not sample_obj:
            LOG.warning("Could not find sample")
            return None
        sample_obj.phenotype_terms = phenotype_terms
        store.session.commit()
        return sample_obj

    @staticmethod
    def add_subject_id_to_sample(
        store: Store, sample_id: str, subject_id: str = "a subject_id"
    ) -> Sample | None:
        """Function for adding a subject_id to a sample in the database."""
        sample_obj: Sample = store.get_sample_by_internal_id(internal_id=sample_id)
        if not sample_obj:
            LOG.warning("Could not find sample")
            return None
        sample_obj.subject_id = subject_id
        store.session.commit()
        return sample_obj

    @classmethod
    def relate_samples(cls, base_store: Store, case: Case, samples: list[Sample]):
        """Utility function to relate many samples to one case."""

        for sample in samples:
            link = base_store.relate_sample(
                case=case, sample=sample, status=PhenotypeStatus.UNKNOWN
            )
            base_store.session.add(link)
            base_store.session.commit()

    @classmethod
    def add_case_with_samples(
        cls,
        base_store: Store,
        case_id: str,
        nr_samples: int,
        sequenced_at: datetime = datetime.now(),
    ) -> Case:
        """Utility function to add one case with many samples and return the case."""

        samples: list[Sample] = cls.add_samples(store=base_store, nr_samples=nr_samples)
        for sample in samples:
            sample.last_sequenced_at: datetime = sequenced_at
        case: Case = cls.add_case(store=base_store, internal_id=case_id, name=case_id)
        cls.relate_samples(base_store=base_store, case=case, samples=samples)
        return case

    @classmethod
    def add_cases_with_samples(
        cls, base_store: Store, nr_cases: int, sequenced_at: datetime
    ) -> list[Case]:
        """Utility function to add many cases with two samples to use in tests."""

        cases: list[Case] = []
        for i in range(nr_cases):
            case: list[Case] = cls.add_case_with_samples(
                base_store, f"f{i}", 2, sequenced_at=sequenced_at
            )
            cases.append(case)
        return cases

    @classmethod
    def ensure_pool(
        cls,
        store: Store,
        customer_id: str = "cust000",
        name: str = "test_pool",
        order: str = "test_order",
        application_tag: str = "dummy_tag",
        application_type: str = "tgs",
        is_external: bool = False,
        is_rna: bool = False,
        delivered_at: datetime = None,
        received_at: datetime = None,
        no_invoice: bool = None,
        invoice_id: int = None,
    ) -> Pool:
        """Utility function to add a pool that can be used in tests."""
        customer_id = customer_id or "cust000"
        customer: Customer = store.get_customer_by_internal_id(customer_internal_id=customer_id)
        if not customer:
            customer = StoreHelpers.ensure_customer(store, customer_id=customer_id)

        application_version = StoreHelpers.ensure_application_version(
            store=store,
            application_tag=application_tag,
            prep_category=application_type,
            is_external=is_external,
            is_rna=is_rna,
        )

        pool = store.add_pool(
            name=name,
            ordered=datetime.now(),
            application_version=application_version,
            customer=customer,
            order=order,
            delivered_at=delivered_at,
            received_at=received_at,
            no_invoice=no_invoice,
            invoice_id=invoice_id,
        )
        store.session.add(pool)
        store.session.commit()
        return pool

    @classmethod
    def ensure_user(
        cls,
        store: Store,
        customer: Customer,
        email: str = "Bob@bobmail.com",
        name: str = "Bob",
        is_admin: bool = False,
    ) -> User:
        """Utility function to add a user that can be used in tests."""
        user: User = store.get_user_by_email(email=email)
        if not user:
            user = store.add_user(customer=customer, email=email, name=name, is_admin=is_admin)
            store.session.add(user)
            store.session.commit()
        return user

    @classmethod
    def ensure_invoice(
        cls,
        store: Store,
        invoice_id: int = 0,
        customer_id: str = "cust000",
        discount: int = 0,
        pools: list[Pool] | None = None,
        samples: list[Sample] | None = None,
        invoiced_at: datetime | None = None,
    ) -> Invoice:
        """Utility function to create an invoice with a costumer and samples or pools."""
        invoice = store.get_invoice_by_entry_id(entry_id=invoice_id)
        if not invoice:
            customer_obj = StoreHelpers.ensure_customer(
                store=store,
                customer_id=customer_id,
            )

            user_obj: User = StoreHelpers.ensure_user(store=store, customer=customer_obj)
            customer_obj.invoice_contact: User = user_obj

            invoice = store.add_invoice(
                customer=customer_obj,
                samples=samples,
                pools=pools,
                comment="just a test invoice",
                discount=discount,
                invoiced_at=invoiced_at,
            )
            store.session.add(invoice)
            store.session.commit()
        return invoice

    @classmethod
    def add_case_with_sample(cls, base_store: Store, case_id: str, sample_id: str) -> Case:
        """Helper function to add a case associated with a sample with the given ids."""

        case = cls.add_case(store=base_store, internal_id=case_id, name=case_id)
        sample = cls.add_sample(store=base_store, internal_id=sample_id)
        cls.add_relationship(store=base_store, sample=sample, case=case)
        return case

    @classmethod
    def add_illumina_flow_cell_and_samples_with_sequencing_metrics(
        cls,
        run_directory_data: IlluminaRunDirectoryData,
        sample_ids: list[str],
        case_ids: list[str],
        store: Store,
    ) -> None:
        """Add an Illumina flow cell and the given samples with sequencing metrics to a store."""
        flow_cell: IlluminaFlowCell = cls.add_illumina_flow_cell(
            store=store,
            flow_cell_id=run_directory_data.id,
        )
        sequencing_run: IlluminaSequencingRun = cls.add_illumina_sequencing_run(
            store=store,
            flow_cell=flow_cell,
            sequencer_type=run_directory_data.sequencer_type,
        )
        for i, sample_id in enumerate(sample_ids):
            cls.add_case(store=store, internal_id=case_ids[i], name=case_ids[i])
            cls.add_sample(store=store, internal_id=sample_id, name=f"sample_{i}")
            cls.relate_samples(
                base_store=store,
                case=store.get_case_by_internal_id(case_ids[i]),
                samples=[store.get_sample_by_internal_id(sample_id)],
            )
            cls.add_illumina_sample_sequencing_metrics_object(
                store=store,
                sample_id=sample_id,
                sequencing_run=sequencing_run,
                lane=i + 1,
            )

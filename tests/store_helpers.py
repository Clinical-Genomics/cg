"""Utility functions to simply add test data in a cg store"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from cg.apps.avatar.api import Avatar
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery, Pipeline
from cg.store import Store, models
from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)

Avatar.get_avatar_urls = lambda internal_id: [str(uuid.uuid4())]
Avatar.get_avatar_url = lambda internal_id: str(uuid.uuid4())
Avatar.is_url_image = lambda: True


class StoreHelpers:
    """Class to hold helper functions that needs to be used all over"""

    @staticmethod
    def ensure_hk_bundle(
        store: HousekeeperAPI, bundle_data: dict, include: bool = False
    ) -> hk_models.Bundle:
        """Utility function to add a bundle of information to a housekeeper api"""
        bundle_exists = False
        if not store.bundles():
            bundle_exists = False
        else:
            for bundle in store.bundles():
                if bundle.name != bundle_data["name"]:
                    continue
                bundle_exists = True
                _bundle = bundle
        if not bundle_exists:
            _bundle, _version = store.add_bundle(bundle_data)
            store.add_commit(_bundle, _version)
        if include:
            store.include(_version)
        return _bundle

    def ensure_hk_version(self, store: HousekeeperAPI, bundle_data: dict) -> hk_models.Version:
        """Utility function to return existing or create an version for tests"""
        _bundle = self.ensure_hk_bundle(store, bundle_data)
        return store.last_version(_bundle.name)

    def ensure_application_version(
        self,
        store: Store,
        application_tag: str = "dummy_tag",
        application_type: str = "wgs",
        is_external: bool = False,
        is_rna: bool = False,
        description: str = None,
        sequencing_depth: int = None,
        is_accredited: bool = False,
    ) -> models.ApplicationVersion:
        """Utility function to return existing or create application version for tests"""
        if is_rna:
            application_tag = "rna_tag"
            application_type = "wts"

        application = store.application(tag=application_tag)
        if not application:
            application = self.add_application(
                store,
                application_tag,
                application_type,
                is_external=is_external,
                description=description,
                is_accredited=is_accredited,
                sequencing_depth=sequencing_depth,
            )

        prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
        version = store.application_version(application, 1)
        if not version:
            version = store.add_version(application, 1, valid_from=datetime.now(), prices=prices)

            store.add_commit(version)
        return version

    def ensure_application(
        self,
        store: Store,
        tag: str,
        application_type: str = "wgs",
        description: str = "dummy_description",
        is_archived: bool = False,
    ) -> models.Application:
        """Ensure that application exists in store"""
        application: models.Application = store.application(tag=tag)
        if not application:
            application: models.Application = self.add_application(
                store=store,
                application_tag=tag,
                application_type=application_type,
                description=description,
                is_archived=is_archived,
            )
        return application

    @staticmethod
    def add_application(
        store: Store,
        application_tag: str = "dummy_tag",
        application_type: str = "wgs",
        description: str = None,
        is_archived: bool = False,
        is_accredited: bool = False,
        is_external: bool = False,
        min_sequencing_depth: int = 30,
        **kwargs,
    ) -> models.Application:
        """Utility function to add a application to a store"""
        application = store.application(tag=application_tag)
        if application:
            return application

        if not description:
            description = "dummy_description"
        application = store.add_application(
            tag=application_tag,
            category=application_type,
            description=description,
            is_archived=is_archived,
            percent_kth=80,
            percent_reads_guaranteed=75,
            is_accredited=is_accredited,
            limitations="A limitation",
            is_external=is_external,
            min_sequencing_depth=min_sequencing_depth,
            **kwargs,
        )
        store.add_commit(application)
        return application

    @staticmethod
    def ensure_bed_version(store: Store, bed_name: str = "dummy_bed") -> models.ApplicationVersion:
        """Utility function to return existing or create bed version for tests"""
        bed = store.bed(name=bed_name)
        if not bed:
            bed = store.add_bed(name=bed_name)
            store.add_commit(bed)

        version = store.latest_bed_version(bed_name)
        if not version:
            version = store.add_bed_version(bed, 1, "dummy_filename", shortname=bed_name)
            store.add_commit(version)
        return version

    @staticmethod
    def ensure_customer(
        store: Store,
        customer_id: str = "cust000",
        name: str = "Production",
        scout_access: bool = False,
        customer_group: str = "all_customers",
    ) -> models.Customer:
        """Utility function to return existing or create customer for tests"""
        customer_group_id = customer_group or customer_id + "_group"
        customer_group = store.customer_group(customer_group_id)
        if not customer_group:
            customer_group = store.add_customer_group(customer_group_id, customer_group_id)

        customer = store.customer(customer_id)

        if not customer:
            customer = store.add_customer(
                internal_id=customer_id,
                name=name,
                scout_access=scout_access,
                customer_group=customer_group,
                invoice_address="Test street",
                invoice_reference="ABCDEF",
            )
            store.add_commit(customer)
        return customer

    def add_analysis(
        self,
        store: Store,
        case: models.Family = None,
        started_at: datetime = None,
        completed_at: datetime = None,
        uploaded_at: datetime = None,
        upload_started: datetime = None,
        delivery_reported_at: datetime = None,
        cleaned_at: datetime = None,
        pipeline: Pipeline = Pipeline.BALSAMIC,
        pipeline_version: str = "1.0",
        data_delivery: DataDelivery = DataDelivery.FASTQ_QC,
        uploading: bool = False,
        config_path: str = None,
    ) -> models.Analysis:
        """Utility function to add an analysis for tests"""

        if not case:
            case = self.add_case(store, data_analysis=pipeline, data_delivery=data_delivery)

        analysis = store.add_analysis(pipeline=pipeline, version=pipeline_version)

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
        if pipeline:
            analysis.pipeline = str(pipeline)

        analysis.limitations = "A limitation"
        analysis.family = case
        store.add_commit(analysis)
        return analysis

    def add_sample(
        self,
        store: Store,
        sample_id: str = None,
        internal_id: str = None,
        gender: str = "female",
        is_tumour: bool = False,
        is_rna: bool = False,
        is_external: bool = False,
        application_tag: str = "dummy_tag",
        application_type: str = "tgs",
        customer_name: str = None,
        reads: int = None,
        loqusdb_id: str = None,
        ticket: int = None,
        **kwargs,
    ) -> models.Sample:
        """Utility function to add a sample to use in tests"""
        customer_name = customer_name or "cust000"
        sample_name = sample_id or "sample_test"
        customer = self.ensure_customer(store, customer_name)
        application_version = self.ensure_application_version(
            store,
            application_tag=application_tag,
            application_type=application_type,
            is_external=is_external,
            is_rna=is_rna,
        )
        application_version_id = application_version.id
        sample = store.add_sample(
            name=sample_name,
            sex=gender,
            tumour=is_tumour,
            reads=reads,
            ticket=ticket,
        )

        sample.application_version_id = application_version_id
        sample.customer = customer
        sample.is_external = is_external
        sample.ordered_at = datetime.now()

        if loqusdb_id:
            sample.loqusdb_id = loqusdb_id

        if kwargs.get("delivered_at"):
            sample.delivered_at = kwargs["delivered_at"]

        if kwargs.get("received_at"):
            sample.received_at = kwargs["received_at"]

        if kwargs.get("prepared_at"):
            sample.prepared_at = kwargs["prepared_at"]

        if kwargs.get("sequenced_at"):
            sample.sequenced_at = kwargs["sequenced_at"]

        if kwargs.get("capture_kit"):
            sample.capture_kit = kwargs["capture_kit"]

        if kwargs.get("flowcell"):
            sample.flowcells.append(kwargs["flowcell"])

        if internal_id:
            sample.internal_id = internal_id

        if kwargs.get("no_invoice"):
            sample.no_invoice = kwargs["no_invoice"]

        store.add_commit(sample)
        return sample

    def ensure_panel(
        self, store: Store, panel_id: str = "panel_test", customer_id: str = "cust000"
    ) -> models.Panel:
        """Utility function to add a panel to use in tests"""
        customer = self.ensure_customer(store, customer_id)
        panel = store.panel(panel_id)
        if not panel:
            panel = store.add_panel(
                customer=customer,
                name=panel_id,
                abbrev=panel_id,
                version=1.0,
                date=datetime.now(),
                genes=1,
            )
            store.add_commit(panel)
        return panel

    def add_case(
        self,
        store: Store,
        case_id: str = "case_test",
        data_analysis: Pipeline = Pipeline.MIP_DNA,
        data_delivery: DataDelivery = DataDelivery.SCOUT,
        action: str = None,
        internal_id: str = None,
        customer_id: str = "cust000",
        panels: List = ["panel_test"],
        case_obj: models.Family = None,
    ) -> models.Family:
        """Utility function to add a case to use in tests,
        If no case object is used a autogenerated case id will be used

        """
        customer = self.ensure_customer(store, customer_id)
        if case_obj:
            panels = case_obj.panels
        for panel_name in panels:
            self.ensure_panel(store, panel_id=panel_name, customer_id=customer_id)

        if not case_obj:
            case_obj: Optional[models.Family] = store.family(internal_id=case_id)
        if not case_obj:
            case_obj = store.add_case(
                data_analysis=data_analysis,
                data_delivery=data_delivery,
                name=case_id,
                panels=panels,
            )
        if action:
            case_obj.action = action
        if internal_id:
            case_obj.internal_id = internal_id

        case_obj.customer = customer
        store.add_commit(case_obj)
        return case_obj

    @staticmethod
    def ensure_case(
        store: Store,
        name: str,
        customer: models.Customer,
        data_analysis: Pipeline,
        data_delivery: DataDelivery,
    ):
        case = store.find_family(customer=customer, name=name)
        if not case:
            case = store.add_case(
                data_analysis=data_analysis,
                data_delivery=data_delivery,
                name=name,
                panels=None,
            )
            case.customer = customer
        return case

    def ensure_case_from_dict(
        self,
        store: Store,
        case_info: dict,
        app_tag: str = None,
        ordered_at: datetime = None,
        completed_at: datetime = None,
        created_at: datetime = datetime.now(),
    ):
        """Load a case with samples and link relations"""
        customer_obj = self.ensure_customer(store)
        case_obj = store.Family(
            name=case_info["name"],
            panels=case_info["panels"],
            internal_id=case_info["internal_id"],
            ordered_at=ordered_at,
            data_analysis=case_info.get("data_analysis", str(Pipeline.MIP_DNA)),
            data_delivery=case_info.get("data_delivery", str(DataDelivery.SCOUT)),
            created_at=created_at,
            action=case_info.get("action"),
        )

        case_obj = self.add_case(store, case_obj=case_obj, customer_id=customer_obj.internal_id)

        app_tag = app_tag or "WGTPCFC030"
        app_type = case_info.get("application_type", "wgs")
        self.ensure_application_version(store, application_tag=app_tag)

        sample_objs = {}
        for sample_data in case_info["samples"]:
            sample_id = sample_data["internal_id"]
            sample_obj = self.add_sample(
                store,
                customer_name=sample_data["name"],
                gender=sample_data["sex"],
                sample_id=sample_data.get("name"),
                internal_id=sample_id,
                application_type=app_type,
                ticket=sample_data["ticket_number"],
                reads=sample_data["reads"],
                capture_kit=sample_data["capture_kit"],
            )
            sample_objs[sample_id] = sample_obj

        for sample_data in case_info["samples"]:
            sample_obj = sample_objs[sample_data["internal_id"]]
            father = None
            if sample_data.get("father"):
                father = sample_objs[sample_data["father"]]
            mother = None
            if sample_data.get("mother"):
                mother = sample_objs[sample_data["mother"]]
            self.add_relationship(
                store,
                case=case_obj,
                sample=sample_obj,
                status=sample_data.get("status", "unknown"),
                father=father,
                mother=mother,
            )

        self.add_analysis(
            store,
            pipeline=Pipeline.MIP_DNA,
            case=case_obj,
            completed_at=completed_at or datetime.now(),
        )
        return case_obj

    @staticmethod
    def add_organism(
        store: Store,
        internal_id: str = "organism_test",
        name: str = "organism_name",
        reference_genome: str = "reference_genome_test",
    ) -> models.Organism:
        """Utility function to add an organism to use in tests"""
        organism = store.add_organism(
            internal_id=internal_id, name=name, reference_genome=reference_genome
        )
        return organism

    def ensure_organism(
        self,
        store: Store,
        organism_id: str = "organism_test",
        name: str = "organism_name",
        reference_genome: str = "reference_genome_test",
    ) -> models.Organism:
        """Utility function to add an organism to use in tests"""
        organism = self.add_organism(
            store, internal_id=organism_id, name=name, reference_genome=reference_genome
        )
        store.add_commit(organism)
        return organism

    def add_microbial_sample(
        self,
        store: Store,
        sample_id: str = "microbial_sample_id",
        priority: str = "research",
        name: str = "microbial_name_test",
        organism: models.Organism = None,
        comment: str = "comment",
        ticket: int = 123456,
    ) -> models.Sample:
        """Utility function to add a sample to use in tests"""
        customer = self.ensure_customer(store, "cust_test")
        application_version = self.ensure_application_version(store)
        if not organism:
            organism = self.ensure_organism(store)

        sample = store.add_sample(
            application_version=application_version,
            comment=comment,
            internal_id=sample_id,
            name=name,
            organism=organism,
            priority=priority,
            reads=6000000,
            sex="unknown",
            ticket=ticket,
        )
        sample.customer = customer
        case = self.ensure_case(
            store=store,
            name=str(ticket),
            customer=customer,
            data_analysis=Pipeline.MICROSALT,
            data_delivery=DataDelivery.FASTQ_QC,
        )
        self.add_relationship(store=store, case=case, sample=sample)
        return sample

    def add_samples(self, store: Store, nr_samples: int = 5) -> list:
        """Utility function to add a number of samples to use in tests"""
        nr_samples = max(nr_samples, 2)
        return [self.add_sample(store, str(sample_id)) for sample_id in range(1, nr_samples)]

    @staticmethod
    def add_flowcell(
        store: Store,
        flowcell_id: str = "flowcell_test",
        archived_at: datetime = None,
        samples: list = None,
        status: str = None,
    ) -> models.Flowcell:
        """Utility function to set a flowcell to use in tests"""
        flowcell_obj = store.add_flowcell(
            name=flowcell_id,
            sequencer="dummy_sequencer",
            sequencer_type="hiseqx",
            date=datetime.now(),
        )
        flowcell_obj.archived_at = archived_at
        if samples:
            flowcell_obj.samples = samples
        if status:
            flowcell_obj.status = status

        store.add_commit(flowcell_obj)
        return flowcell_obj

    @staticmethod
    def add_relationship(
        store: Store,
        sample: models.Sample,
        case: models.Family,
        status: str = "unknown",
        father: models.Sample = None,
        mother: models.Sample = None,
    ) -> models.FamilySample:
        """Utility function to link a sample to a case"""
        link = store.relate_sample(
            sample=sample, family=case, status=status, father=father, mother=mother
        )
        store.add_commit(link)
        return link

    @staticmethod
    def add_synopsis_to_case(
        store: Store, case_id: str, synopsis: str = "a synopsis"
    ) -> Optional[models.Family]:
        """Function for adding a synopsis to a case in the database"""
        case_obj: models.Family = store.family(internal_id=case_id)
        if not case_obj:
            LOG.warning("Could not find case")
            return None
        case_obj._synopsis = synopsis
        store.add_commit(case_obj)
        return case_obj

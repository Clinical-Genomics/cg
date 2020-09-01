"""Utility functions to simply add test data in a cg store"""
import logging
from datetime import datetime
from typing import List

from housekeeper.store import models as hk_models

from cg.apps.hk import HousekeeperAPI
from cg.store import Store, models

LOG = logging.getLogger(__name__)


class StoreHelpers:
    """Class to hold helper functions that needs to be used all over"""

    @staticmethod
    def ensure_hk_bundle(store: HousekeeperAPI, bundle_data: dict) -> hk_models.Bundle:
        """Utility function to add a bundle of information to a housekeeper api"""
        bundle_exists = False
        for bundle in store.bundles():
            if bundle.name != bundle_data["name"]:
                continue
            bundle_exists = True
        if not bundle_exists:
            print("No bundle found")
            _bundle, _version = store.add_bundle(bundle_data)
            print("Add bundle with name %s" % bundle_data["name"])
            store.add_commit(_bundle, _version)
        return _bundle

    def ensure_hk_version(self, store: HousekeeperAPI, bundle_data: dict) -> hk_models.Version:
        """Utility function to return existing or create an version for tests"""
        _bundle = self.ensure_hk_bundle(store, bundle_data)
        _version = store.last_version(_bundle.name)
        return _version

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

    @staticmethod
    def add_application(
        store: Store,
        application_tag: str = "dummy_tag",
        application_type: str = "wgs",
        description: str = None,
        is_accredited: bool = False,
        is_external: bool = False,
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
            percent_kth=80,
            is_accredited=is_accredited,
            limitations="A limitation",
            is_external=is_external,
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
        family: models.Family = None,
        started_at: datetime = None,
        completed_at: datetime = None,
        uploaded_at: datetime = None,
        upload_started: datetime = None,
        delivery_reported_at: datetime = None,
        cleaned_at: datetime = None,
        pipeline: str = "dummy_pipeline",
        pipeline_version: str = "1.0",
        uploading: bool = False,
        config_path: str = None,
    ) -> models.Analysis:
        """Utility function to add an analysis for tests"""

        if not family:
            family = self.add_family(store)

        analysis = store.add_analysis(pipeline=pipeline, version=pipeline_version)

        if started_at:
            analysis.started_at = started_at
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
            analysis.pipeline = pipeline

        analysis.limitations = "A limitation"
        analysis.family = family
        store.add_commit(analysis)
        return analysis

    def add_sample(
        self,
        store: Store,
        sample_id: str = "sample_test",
        internal_id: str = None,
        gender: str = "female",
        is_tumour: bool = False,
        is_rna: bool = False,
        is_external: bool = False,
        data_analysis: str = "balsamic",
        application_tag: str = "dummy_tag",
        application_type: str = "tgs",
        customer_name: str = None,
        reads: int = None,
        loqus_id: str = None,
        **kwargs,
    ) -> models.Sample:
        """Utility function to add a sample to use in tests"""
        customer_name = customer_name or "cust000"
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
            name=sample_id,
            sex=gender,
            tumour=is_tumour,
            sequenced_at=datetime.now(),
            data_analysis=data_analysis,
            reads=reads,
        )

        sample.application_version_id = application_version_id
        sample.customer = customer
        # print("is_external: %s" % is_external)
        sample.is_external = is_external

        if loqus_id:
            sample.loqusdb_id = loqus_id

        if kwargs.get("delivered_at"):
            sample.delivered_at = kwargs["delivered_at"]

        if kwargs.get("received_at"):
            sample.received_at = kwargs["received_at"]

        if kwargs.get("prepared_at"):
            sample.received_at = kwargs["prepared_at"]

        if kwargs.get("flowcell"):
            sample.flowcells.append(kwargs["flowcell"])

        if internal_id:
            sample.internal_id = internal_id

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

    def add_family(
        self,
        store: Store,
        family_id: str = "family_test",
        internal_id: str = None,
        customer_id: str = "cust000",
        panels: List = None,
        family_obj: models.Family = None,
    ) -> models.Family:
        """Utility function to add a family to use in tests,
        If no family object is used a autogenerated family id will be used

        """
        customer = self.ensure_customer(store, customer_id)
        if family_obj:
            panels = family_obj.panels
        if not panels:
            panels = ["panel_test"]
        for panel_name in panels:
            self.ensure_panel(store, panel_id=panel_name, customer_id=customer_id)

        if not family_obj:
            family_obj = store.add_family(name=family_id, panels=panels)

        if internal_id:
            family_obj.internal_id = internal_id

        # print("Adding family with name %s (%s)" % (family_obj.name, family_obj.internal_id))
        family_obj.customer = customer
        store.add_commit(family_obj)
        return family_obj

    def ensure_family(
        self,
        store: Store,
        family_info: dict,
        app_tag: str = None,
        ordered_at: datetime = None,
        completed_at: datetime = None,
    ):
        """Load a family with samples and link relations"""
        customer_obj = self.ensure_customer(store)
        family_obj = store.Family(
            name=family_info["name"],
            panels=family_info["panels"],
            internal_id=family_info["internal_id"],
            priority="standard",
            ordered_at=ordered_at,
        )

        family_obj = self.add_family(
            store, family_obj=family_obj, customer_id=customer_obj.internal_id
        )

        app_tag = app_tag or "WGTPCFC030"
        app_type = family_info.get("application_type", "wgs")
        self.ensure_application_version(store, application_tag=app_tag)
        data_analysis = family_info.get("data_analysis", "mip")
        sample_objs = {}
        for sample_data in family_info["samples"]:
            sample_id = sample_data["internal_id"]
            sample_obj = self.add_sample(
                store,
                customer_name=sample_data["name"],
                gender=sample_data["sex"],
                internal_id=sample_id,
                data_analysis=data_analysis,
                application_type=app_type,
                ticket=sample_data["ticket_number"],
                reads=sample_data["reads"],
            )
            sample_objs[sample_id] = sample_obj

        for sample_data in family_info["samples"]:
            sample_obj = sample_objs[sample_data["internal_id"]]
            father = None
            if sample_data.get("father"):
                father = sample_objs[sample_data["father"]]
            mother = None
            if sample_data.get("mother"):
                mother = sample_objs[sample_data["mother"]]
            self.add_relationship(
                store,
                family=family_obj,
                sample=sample_obj,
                status=sample_data.get("status", "unknown"),
                father=father,
                mother=mother,
            )

        self.add_analysis(store, pipeline="pipeline", family=family_obj, completed_at=completed_at)
        return family_obj

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
        sample_id: str = "microbial_sample_test",
        priority: str = "research",
        name: str = "microbial_name_test",
        organism: models.Organism = None,
    ) -> models.MicrobialSample:
        """Utility function to add a sample to use in tests"""
        customer = self.ensure_customer(store)
        application_version = self.ensure_application_version(store)
        if not organism:
            organism = self.ensure_organism(store)

        sample = store.add_microbial_sample(
            name=name,
            priority=priority,
            organism=organism,
            internal_id=sample_id,
            reference_genome=organism.reference_genome,
            application_version=application_version,
        )
        sample.customer = customer
        return sample

    def ensure_microbial_order(
        self,
        store: Store,
        order_id: str = "microbial_order_test",
        name: str = "microbial_name_test",
        customer_id: str = "cust_test",
    ) -> models.MicrobialOrder:
        """Utility function add a microbial order and sample"""
        customer = self.ensure_customer(store, customer_id)
        order = store.add_microbial_order(
            customer=customer,
            internal_id=order_id,
            name=name,
            ordered=datetime.now(),
            ticket_number=123456,
        )
        store.add_commit(order)

        return order

    def add_microbial_sample_and_order(
        self,
        store: Store,
        order_id: str = "microbial_order_test",
        sample_id: str = "microbial_sample_test",
        customer_id: str = "cust_test",
    ) -> models.MicrobialSample:
        """Utility add a order and a sample to use in tests"""
        self.ensure_application_version(store)
        self.ensure_customer(store, customer_id)
        organism = self.ensure_organism(store)
        order = self.ensure_microbial_order(store)
        sample = self.add_microbial_sample(store, organism=organism)
        sample.microbial_order_id = order.id
        store.add_commit(sample)
        return sample

    def add_samples(self, store: Store, nr_samples: int = 5) -> list:
        """Utility function to add a number of samples to use in tests"""
        samples = []
        if nr_samples < 2:
            nr_samples = 2
        for sample_id in range(1, nr_samples):
            samples.append(self.add_sample(store, str(sample_id)))
        return samples

    @staticmethod
    def add_flowcell(
        store: Store,
        flowcell_id: str = "flowcell_test",
        archived_at: datetime = None,
        samples: list = None,
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

        store.add_commit(flowcell_obj)
        return flowcell_obj

    @staticmethod
    def add_relationship(
        store: Store,
        sample: models.Sample,
        family: models.Family,
        status: str = "unknown",
        father: models.Sample = None,
        mother: models.Sample = None,
    ) -> models.FamilySample:
        """Utility function to link a sample to a family"""
        link = store.relate_sample(
            sample=sample, family=family, status=status, father=father, mother=mother
        )
        store.add_commit(link)
        return link

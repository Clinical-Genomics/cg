"""Utility functions to simply add test data in a cg store"""
import logging
from datetime import datetime
from typing import List, Optional

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery, Pipeline
from cg.constants.pedigree import Pedigree
from cg.constants.priority import PriorityTerms
from cg.constants.sequencing import Sequencers
from cg.constants.subject import Gender, PhenotypeStatus
from cg.store import Store, models
from housekeeper.store import models as hk_models

from cg.store.models import Flowcell

LOG = logging.getLogger(__name__)


class StoreHelpers:
    """Class to hold helper functions that needs to be used all over"""

    @staticmethod
    def ensure_hk_bundle(
        store: HousekeeperAPI, bundle_data: dict, include: bool = False
    ) -> hk_models.Bundle:
        """Utility function to add a bundle of information to a housekeeper api"""

        bundle_exists = False
        for bundle in store.bundles():
            if bundle.name != bundle_data["name"]:
                continue
            bundle_exists = True
            _bundle = bundle
            break

        if not bundle_exists:
            _bundle, _version = store.add_bundle(bundle_data)
            store.add_commit(_bundle, _version)

        if include:
            store.include(_version)

        return _bundle

    @staticmethod
    def ensure_hk_version(store: HousekeeperAPI, bundle_data: dict) -> hk_models.Version:
        """Utility function to return existing or create an version for tests"""
        _bundle = StoreHelpers.ensure_hk_bundle(store, bundle_data)
        return store.last_version(_bundle.name)

    @staticmethod
    def ensure_application_version(
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
            application = StoreHelpers.add_application(
                store,
                application_tag,
                application_type,
                is_external=is_external,
                description=description,
                is_accredited=is_accredited,
                sequencing_depth=sequencing_depth,
            )

        prices = {
            PriorityTerms.STANDARD: 10,
            PriorityTerms.PRIORITY: 20,
            PriorityTerms.EXPRESS: 30,
            PriorityTerms.RESEARCH: 5,
        }
        version = store.application_version(application, 1)
        if not version:
            version = store.add_version(application, 1, valid_from=datetime.now(), prices=prices)

            store.add_commit(version)
        return version

    @staticmethod
    def ensure_application(
        store: Store,
        tag: str,
        application_type: str = "wgs",
        description: str = "dummy_description",
        is_archived: bool = False,
    ) -> models.Application:
        """Ensure that application exists in store"""
        application: models.Application = store.application(tag=tag)
        if not application:
            application: models.Application = StoreHelpers.add_application(
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
        collaboration_id: str = "all_customers",
    ) -> models.Customer:
        """Utility function to return existing or create customer for tests"""
        collaboration = store.collaboration(collaboration_id)
        if not collaboration:
            collaboration = store.add_collaboration(collaboration_id, collaboration_id)

        customer = store.customer(customer_id)

        if not customer:
            customer = store.add_customer(
                internal_id=customer_id,
                name=name,
                scout_access=scout_access,
                invoice_address="Test street",
                invoice_reference="ABCDEF",
            )
            customer.collaborations.append(collaboration)
            store.add_commit(customer)
        return customer

    @staticmethod
    def add_analysis(
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
            case = StoreHelpers.add_case(store, data_analysis=pipeline, data_delivery=data_delivery)

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

    @staticmethod
    def add_sample(
        store: Store,
        application_tag: str = "dummy_tag",
        application_type: str = "tgs",
        control: str = "",
        customer_id: str = None,
        gender: str = Gender.FEMALE,
        is_external: bool = False,
        is_rna: bool = False,
        is_tumour: bool = False,
        reads: int = None,
        name: str = "sample_test",
        original_ticket: str = None,
        **kwargs,
    ) -> models.Sample:
        """Utility function to add a sample to use in tests"""
        customer_id = customer_id or "cust000"
        customer = StoreHelpers.ensure_customer(store, customer_id=customer_id)
        application_version = StoreHelpers.ensure_application_version(
            store=store,
            application_tag=application_tag,
            application_type=application_type,
            is_external=is_external,
            is_rna=is_rna,
        )
        application_version_id = application_version.id
        sample = store.add_sample(
            name=name,
            sex=gender,
            control=control,
            original_ticket=original_ticket,
            tumour=is_tumour,
            reads=reads,
        )

        sample.application_version_id = application_version_id
        sample.customer = customer
        sample.ordered_at = datetime.now()

        for key, value in kwargs.items():
            if key == "flowcell":
                sample.flowcells.append(kwargs["flowcell"])
            elif hasattr(sample, key):
                setattr(sample, key, value)
            else:
                raise AttributeError(f"Unknown sample attribute/feature: {key}, {value}")

        store.add_commit(sample)
        return sample

    @staticmethod
    def ensure_panel(
        store: Store, panel_id: str = "panel_test", customer_id: str = "cust000"
    ) -> models.Panel:
        """Utility function to add a panel to use in tests"""
        customer = StoreHelpers.ensure_customer(store, customer_id)
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

    @staticmethod
    def add_case(
        store: Store,
        name: str = "case_test",
        data_analysis: Pipeline = Pipeline.MIP_DNA,
        data_delivery: DataDelivery = DataDelivery.SCOUT,
        action: str = None,
        internal_id: str = None,
        customer_id: str = "cust000",
        panels: List[str] = [],
        case_obj: models.Family = None,
        ticket: str = "123456",
    ) -> models.Family:
        """Utility function to add a case to use in tests,
        If no case object is used a autogenerated case id will be used.

        """
        if not panels:
            panels: List[str] = ["panel_test"]
        customer = StoreHelpers.ensure_customer(store, customer_id)
        if case_obj:
            panels = case_obj.panels
        for panel_name in panels:
            StoreHelpers.ensure_panel(store=store, panel_id=panel_name, customer_id=customer_id)

        if not case_obj:
            case_obj: Optional[models.Family] = store.family(internal_id=name)
        if not case_obj:
            case_obj = store.add_case(
                data_analysis=data_analysis,
                data_delivery=data_delivery,
                name=name,
                panels=panels,
                ticket=ticket,
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
        name: str = "test-case",
        case_id: str = "blueeagle",
        customer: models.Customer = None,
        data_analysis: Pipeline = Pipeline.MIP_DNA,
        data_delivery: DataDelivery = DataDelivery.SCOUT,
    ):
        if not customer:
            customer = StoreHelpers.ensure_customer(store=store)
        case = store.family(internal_id=case_id) or store.find_family(customer=customer, name=name)
        if not case:
            case = StoreHelpers.add_case(
                store=store,
                data_analysis=data_analysis,
                data_delivery=data_delivery,
                name=name,
                internal_id=case_id,
            )
            case.customer = customer
        return case

    @staticmethod
    def ensure_case_from_dict(
        store: Store,
        case_info: dict,
        app_tag: str = None,
        ordered_at: datetime = None,
        completed_at: datetime = None,
        created_at: datetime = datetime.now(),
    ):
        """Load a case with samples and link relations"""
        customer_obj = StoreHelpers.ensure_customer(store)
        case_obj = store.Family(
            name=case_info["name"],
            panels=case_info["panels"],
            internal_id=case_info["internal_id"],
            ordered_at=ordered_at,
            data_analysis=case_info.get("data_analysis", str(Pipeline.MIP_DNA)),
            data_delivery=case_info.get("data_delivery", str(DataDelivery.SCOUT)),
            created_at=created_at,
            action=case_info.get("action"),
            tickets=case_info["tickets"],
        )

        case_obj = StoreHelpers.add_case(
            store, case_obj=case_obj, customer_id=customer_obj.internal_id
        )

        app_tag = app_tag or "WGSPCFC030"
        app_type = case_info.get("application_type", "wgs")
        StoreHelpers.ensure_application_version(store, application_tag=app_tag)

        sample_objs = {}
        for sample_data in case_info["samples"]:
            sample_id = sample_data["internal_id"]
            sample_obj = StoreHelpers.add_sample(
                store,
                gender=sample_data["sex"],
                name=sample_data.get("name"),
                internal_id=sample_id,
                application_type=app_type,
                application_tag=app_tag,
                original_ticket=sample_data["original_ticket"],
                reads=sample_data["reads"],
                capture_kit=sample_data["capture_kit"],
            )
            sample_objs[sample_id] = sample_obj

        for sample_data in case_info["samples"]:
            sample_obj = sample_objs[sample_data["internal_id"]]
            father = None
            if sample_data.get(Pedigree.FATHER):
                father = sample_objs[sample_data[Pedigree.FATHER]]
            mother = None
            if sample_data.get(Pedigree.MOTHER):
                mother = sample_objs[sample_data[Pedigree.MOTHER]]
            StoreHelpers.add_relationship(
                store,
                case=case_obj,
                sample=sample_obj,
                status=sample_data.get("status", PhenotypeStatus.UNKNOWN),
                father=father,
                mother=mother,
            )

        StoreHelpers.add_analysis(
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
    ) -> models.Organism:
        """Utility function to add an organism to use in tests"""
        organism = StoreHelpers.add_organism(
            store, internal_id=organism_id, name=name, reference_genome=reference_genome
        )
        store.add_commit(organism)
        return organism

    @staticmethod
    def add_microbial_sample(
        store: Store,
        sample_id: str = "microbial_sample_id",
        priority: str = PriorityTerms.RESEARCH,
        name: str = "microbial_name_test",
        organism: models.Organism = None,
        comment: str = "comment",
        ticket: int = 123456,
    ) -> models.Sample:
        """Utility function to add a sample to use in tests"""
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
            sex=Gender.UNKNOWN,
        )
        sample.customer = customer
        case = StoreHelpers.ensure_case(
            store=store,
            name=str(ticket),
            customer=customer,
            data_analysis=Pipeline.MICROSALT,
            data_delivery=DataDelivery.FASTQ_QC,
        )
        StoreHelpers.add_relationship(store=store, case=case, sample=sample)
        return sample

    @staticmethod
    def add_samples(store: Store, nr_samples: int = 5) -> List[models.Sample]:
        """Utility function to add a number of samples to use in tests"""
        nr_samples = max(nr_samples, 2)
        return [
            StoreHelpers.add_sample(store, str(sample_id)) for sample_id in range(1, nr_samples)
        ]

    @staticmethod
    def add_flowcell(
        store: Store,
        flow_cell_id: str = "flowcell_test",
        archived_at: datetime = None,
        sequencer_type: str = Sequencers.HISEQX,
        samples: list = None,
        status: str = None,
        date: datetime = datetime.now(),
    ) -> Flowcell:
        """Utility function to add a flow cell to the store and return an object."""
        flow_cell = store.add_flow_cell(
            flow_cell_id=flow_cell_id,
            sequencer_name="dummy_sequencer",
            sequencer_type=sequencer_type,
            date=date,
        )
        flow_cell.archived_at = archived_at
        if samples:
            flow_cell.samples = samples
        if status:
            flow_cell.status = status

        store.add_commit(flow_cell)
        return flow_cell

    @staticmethod
    def add_relationship(
        store: Store,
        sample: models.Sample,
        case: models.Family,
        status: str = PhenotypeStatus.UNKNOWN,
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
        case_obj.synopsis = synopsis
        store.commit()
        return case_obj

    @staticmethod
    def add_phenotype_groups_to_sample(
        store: Store, sample_id: str, phenotype_groups: [str] = None
    ) -> Optional[models.Sample]:
        """Function for adding a phenotype group to a sample in the database"""
        if phenotype_groups is None:
            phenotype_groups = ["a phenotype group"]
        sample_obj: models.Sample = store.sample(internal_id=sample_id)
        if not sample_obj:
            LOG.warning("Could not find sample")
            return None
        sample_obj.phenotype_groups = phenotype_groups
        store.commit()
        return sample_obj

    @staticmethod
    def add_phenotype_terms_to_sample(
        store: Store, sample_id: str, phenotype_terms: List[str] = []
    ) -> Optional[models.Sample]:
        """Function for adding a phenotype term to a sample in the database."""
        if not phenotype_terms:
            phenotype_terms: List[str] = ["a phenotype term"]
        sample_obj: models.Sample = store.sample(internal_id=sample_id)
        if not sample_obj:
            LOG.warning("Could not find sample")
            return None
        sample_obj.phenotype_terms = phenotype_terms
        store.commit()
        return sample_obj

    @staticmethod
    def add_subject_id_to_sample(
        store: Store, sample_id: str, subject_id: str = "a subject_id"
    ) -> Optional[models.Sample]:
        """Function for adding a subject_id to a sample in the database"""
        sample_obj: models.Sample = store.sample(internal_id=sample_id)
        if not sample_obj:
            LOG.warning("Could not find sample")
            return None
        sample_obj.subject_id = subject_id
        store.commit()
        return sample_obj

    @classmethod
    def relate_samples(cls, base_store: Store, family: str, samples: List[str]):
        """Utility function to relate many samples to one case"""

        for sample in samples:
            base_store.relate_sample(family, sample, PhenotypeStatus.UNKNOWN)

    @classmethod
    def add_case_with_samples(
        cls, base_store: Store, case_name: str, nr_samples: int, sequenced_at: datetime
    ) -> models.Family:
        """Utility function to add one case with many samples and return the case"""

        samples: List[models.Sample] = cls.add_samples(base_store, nr_samples)
        for sample in samples:
            sample.sequenced_at: datetime = sequenced_at
        case: models.Family = cls.add_case(base_store, case_name)
        cls.relate_samples(base_store, case, samples)
        return case

    @classmethod
    def add_cases_with_samples(
        cls, base_store: Store, nr_cases: int, sequenced_at: datetime
    ) -> List[models.Family]:
        """Utility function to add many cases with two samples to use in tests"""

        cases: List[models.Family] = []
        for i in range(nr_cases):
            case: List[models.Family] = cls.add_case_with_samples(
                base_store, f"f{i}", 2, sequenced_at=sequenced_at
            )
            cases.append(case)
        return cases

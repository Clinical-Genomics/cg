from cg.constants.priority import Priority
from cg.constants.constants import PrepCategory, Workflow
from cg.store.models import Case, Sample, Application, ApplicationVersion
from cg.store.store import Store

from tests.conftest import StoreHelpers


class SequencingQCCheckScenarios:
    def __init__(self, store: Store, helpers: StoreHelpers):
        self.store: Store = store
        self.helpers: StoreHelpers = helpers

    def add_sample(
        self,
        prep_category: PrepCategory,
        pass_sequencing_qc: bool,
        priority: Priority,
    ) -> Sample:
        """
        Add a sample to the store with a specified PrepCategory. The sample
        will have reads if pass_sequencing_qc is True.
        """
        application: Application = self.helpers.ensure_application(
            store=self.store, tag="test_tag", target_reads=10, prep_category=prep_category
        )
        application_version: ApplicationVersion = self.helpers.ensure_application_version(
            store=self.store, application_tag=application.tag, version=0
        )
        reads: int = 10 if pass_sequencing_qc else 0
        sample: Sample = self.helpers.add_sample(store=self.store, reads=reads, priority=priority)

        sample.application_version = application_version
        return sample

    def add_case(
        self,
        pass_sequencing_qc: bool,
        prep_category: PrepCategory,
        workflow: Workflow,
        priority: Priority = Priority.standard,
    ) -> Case:
        """
        Add a case to the store. The case will have a sample with the specified PrepCategory. The
        sample will have reads if pass_sequencing_qc is True. The case will have the specified
        workflow.
        """
        case: Case = self.helpers.add_case(
            store=self.store, data_analysis=workflow, priority=priority
        )
        sample: Sample = self.add_sample(
            prep_category=prep_category, pass_sequencing_qc=pass_sequencing_qc, priority=priority
        )
        self.helpers.add_relationship(store=self.store, sample=sample, case=case)
        return case

    def get_sample_scenario(
        self, priority: Priority, prep_category: PrepCategory, pass_sequencing_qc: bool
    ) -> Sample:
        """
        Create a sample scenario. The sample will have reads if pass_sequencing_qc is True. The
        sample will have the specified PrepCategory.
        """
        return self.add_sample(
            prep_category=prep_category, pass_sequencing_qc=pass_sequencing_qc, priority=priority
        )

    def get_case_scenario(
        self,
        priority: Priority,
        pass_sequencing_qc: bool,
        prep_category: PrepCategory,
        workflow: Workflow,
    ) -> Case:
        """
        Create a case scenario. The case will have a sample with the specified PrepCategory. The
        sample will have reads if pass_sequencing_qc is True. The case will have the specified
        workflow.
        """
        return self.add_case(
            pass_sequencing_qc=pass_sequencing_qc,
            prep_category=prep_category,
            workflow=workflow,
            priority=priority,
        )

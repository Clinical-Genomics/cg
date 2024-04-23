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
    ) -> Sample:
        """
        Add a sample to the store.

        Args:
            prep_category: The prep category of the sample.
            pass_sequencing_qc: Whether the sample has reads or not.

        Returns:
            Sample: The added sample.
        """
        application: Application = self.helpers.ensure_application(
            store=self.store, tag="test_tag", target_reads=10, prep_category=prep_category
        )
        application_version: ApplicationVersion = self.helpers.ensure_application_version(
            store=self.store, application_tag=application.tag, version=0
        )
        if pass_sequencing_qc:
            sample: Sample = self.helpers.add_sample(
                store=self.store, reads=10, priority=Priority.standard
            )
        else:
            sample: Sample = self.helpers.add_sample(
                store=self.store, reads=0, priority=Priority.standard
            )

        sample.application_version = application_version
        return sample

    def add_express_sample(self, prep_category: PrepCategory, pass_sequencing_qc: bool) -> Sample:
        """
        Add an express sample to the store.

        Args:
            prep_category: The prep category of the sample.
            pass_sequencing_qc: Whether the sample has reads or not.

        Returns:
            Sample: The added express sample.
        """
        express_sample: Sample = self.add_sample(
            prep_category=prep_category, pass_sequencing_qc=pass_sequencing_qc
        )
        express_sample.priority = Priority.express
        if not pass_sequencing_qc:
            express_sample.reads = 4
        return express_sample

    def add_case(
        self, pass_sequencing_qc: bool, prep_category: PrepCategory, workflow: Workflow
    ) -> Case:
        """
        Add a case to the store.

        Args:
            pass_sequencing_qc: Whether the sample has reads or not.
            prep_category: The prep category of the sample.
            workflow: The workflow of the case.

        Returns:
            Case: The added case.
        """
        case: Case = self.helpers.add_case(store=self.store, data_analysis=workflow)
        case.priority = Priority.standard
        sample: Sample = self.add_sample(
            prep_category=prep_category, pass_sequencing_qc=pass_sequencing_qc
        )
        self.helpers.add_relationship(store=self.store, sample=sample, case=case)
        return case

    def add_express_case(
        self, pass_sequencing_qc: bool, prep_category: PrepCategory, workflow: Workflow
    ) -> Case:
        """
        Add an express case to the store.

        Args:
            pass_sequencing_qc: Whether the sample has reads or not.
            prep_category: The prep category of the sample.
            workflow: The workflow of the case.

        Returns:
            Case: The added express case.
        """
        express_case: Case = self.helpers.add_case(store=self.store, data_analysis=workflow)
        express_case.priority = Priority.express
        express_sample: Sample = self.add_express_sample(
            prep_category=prep_category, pass_sequencing_qc=pass_sequencing_qc
        )
        self.helpers.add_relationship(store=self.store, sample=express_sample, case=express_case)
        return express_case

    def sample_scenario(
        self, priority: Priority, prep_category: PrepCategory, pass_sequencing_qc: bool
    ) -> Sample:
        """
        Create a sample scenario.

        Args:
            priority: The priority of the sample.
            prep_category: The prep category of the sample.
            pass_sequencing_qc: Whether the sample has reads or not.

        Returns:
            Sample: A sample instance.
        """
        if priority == Priority.express:
            return self.add_express_sample(
                prep_category=prep_category, pass_sequencing_qc=pass_sequencing_qc
            )
        return self.add_sample(prep_category=prep_category, pass_sequencing_qc=pass_sequencing_qc)

    def ready_made_library_sample_scenario(
        self, pass_sequencing_qc: bool, priority: Priority
    ) -> Sample:
        """
        Create a ready-made library sample scenario.

        Args:
            pass_sequencing_qc: Whether the sample has reads or not.
            priority: The priority of the sample.

        Returns:
            Sample: A ready-made library sample instance.
        """
        sample: Sample = self.sample_scenario(
            priority=priority,
            prep_category=PrepCategory.READY_MADE_LIBRARY,
            pass_sequencing_qc=pass_sequencing_qc,
        )
        if not pass_sequencing_qc:
            sample.reads = 0
        return sample

    def case_scenario(
        self,
        priority: Priority,
        pass_sequencing_qc: bool,
        prep_category: PrepCategory,
        workflow: Workflow,
    ) -> Case:
        """
        Create a case scenario.

        Args:
            priority: The priority of the case.
            pass_sequencing_qc: Whether the sample has reads or not.
            prep_category: The prep category of the sample.
            workflow: The workflow of the case.

        Returns:
            Case: A case instance.
        """
        if priority == Priority.express:
            return self.add_express_case(
                pass_sequencing_qc=pass_sequencing_qc,
                prep_category=prep_category,
                workflow=workflow,
            )
        return self.add_case(
            pass_sequencing_qc=pass_sequencing_qc, prep_category=prep_category, workflow=workflow
        )

from cg.constants.constants import DNA_PREP_CATEGORIES, Workflow
from cg.exc import CgDataError
from cg.store.models import Case, Customer, Sample
from cg.store.store import Store


class RNADNACollectionService:
    def __init__(self, store: Store):
        self.store = store

    def get_related_dna_cases_from_rna_case(self, rna_case: Case) -> list[Case]:
        """Return a list of DNA cases related to the samples of an RNA case."""
        dna_cases: list[Case] = []
        for sample in rna_case.samples:
            dna_cases.extend(self._get_related_dna_cases_from_rna_sample(sample))
        return dna_cases

    def _get_related_dna_cases_from_rna_sample(self, rna_sample: Sample) -> list[Case]:
        """Return a list of DNA cases related to an RNA sample."""
        if not rna_sample.subject_id:
            raise CgDataError(
                f"Failed to link RNA sample {rna_sample.internal_id} to DNA samples - subject_id field is empty."
            )

        collaborators: set[Customer] = rna_sample.customer.collaborators
        related_dna_samples: list[Sample] = self.store.get_related_samples(
            sample_internal_id=rna_sample.internal_id,
            prep_categories=DNA_PREP_CATEGORIES,
            collaborators=collaborators,
        )

        if len(related_dna_samples) != 1:
            raise CgDataError(
                f"Failed to upload files for RNA case: unexpected number of DNA sample matches for subject_id: "
                f"{rna_sample.subject_id}. Number of matches: {len(related_dna_samples)} "
            )
        dna_sample: Sample = related_dna_samples[0]
        workflows = [
            Workflow.MIP_DNA,
            Workflow.BALSAMIC,
            Workflow.BALSAMIC_UMI,
        ]
        dna_cases: list[Case] = self.store.get_related_cases(
            sample_internal_id=dna_sample.internal_id,
            workflows=workflows,
            collaborators=collaborators,
        )

        return dna_cases

import logging

from cg.constants import DNA_PREP_CATEGORIES, DNA_WORKFLOWS_WITH_SCOUT_UPLOAD
from cg.exc import CgDataError
from cg.store.models import Case, Customer, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class RNADNACollectionsService:
    """Service that returns all or just uploaded related DNA cases for a given RNA case."""

    def __init__(self, store: Store):
        self.store = store

    def get_uploaded_related_dna_cases(self, rna_case: Case) -> list[Case]:
        """Returns all uploaded DNA cases related to the specified RNA case."""
        dna_cases: set[Case] = self.get_related_dna_cases_from_rna_case(rna_case=rna_case)
        uploaded_dna_cases: list[Case] = []
        for dna_case in dna_cases:
            if dna_case.is_uploaded:
                uploaded_dna_cases.append(dna_case)
            else:
                LOG.warning(f"Related DNA case {dna_case.internal_id} has not been completed.")
        return uploaded_dna_cases

    def get_related_dna_cases_from_rna_case(self, rna_case: Case) -> set[Case]:
        """Return a list of unique DNA cases related to the samples of an RNA case."""
        dna_cases: set[Case] = set()
        for sample in rna_case.samples:
            dna_cases.update(self._get_related_dna_cases_from_rna_sample(sample))
        return dna_cases

    def _get_related_dna_cases_from_rna_sample(self, rna_sample: Sample) -> list[Case]:
        """Return a list of DNA cases related to an RNA sample."""
        # TODO How to do error handling? if no subject_id rna results shouldn't be uploaded.
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

        # TODO same issue here - rna case shouldn't be uploaded in the first place
        if len(related_dna_samples) != 1:
            raise CgDataError(
                f"Failed to upload files for RNA case: unexpected number of DNA sample matches for subject_id: "
                f"{rna_sample.subject_id}. Number of matches: {len(related_dna_samples)} "
            )
        dna_sample: Sample = related_dna_samples[0]

        dna_cases: list[Case] = self.store.get_related_cases(
            sample_internal_id=dna_sample.internal_id,
            workflows=DNA_WORKFLOWS_WITH_SCOUT_UPLOAD,
            collaborators=collaborators,
        )

        return dna_cases

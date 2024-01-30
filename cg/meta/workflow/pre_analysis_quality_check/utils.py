from cg.constants.constants import PrepCategory


def all_samples_are_ready_made_libraries(self) -> bool:
    """
    Check if all samples in case are ready made libraries.

    Returns:
        bool: True if all samples are ready made libraries, False otherwise.

    """
    return all(sample.prep_category == PrepCategory.ready_made_library for sample in self.samples)

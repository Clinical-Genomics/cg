from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.services.order_validation_service.workflows.balsamic.models.sample import BalsamicSample
from cg.store.models import Application
from cg.store.store import Store


def is_sample_missing_capture_kit(sample: BalsamicSample, store: Store) -> bool:
    application: Application | None = store.get_application_by_tag(sample.application)
    return (
        application
        and application.prep_category == SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING
        and not sample.capture_kit
    )

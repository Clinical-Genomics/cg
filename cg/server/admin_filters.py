from flask_admin.model.filters import BaseFilter

from cg.store.models import InstrumentRun, PacbioSequencingRun


class PacbioRunNameFilter(BaseFilter):
    name = "PacBio Run Name"

    def __init__(self, name=None):
        super().__init__(name)

    def apply(self, query, value):
        # Manually join PacbioInstrumentRun to filter only those
        return query.join(PacbioSequencingRun, InstrumentRun.id == PacbioSequencingRun.id).filter(
            PacbioSequencingRun.run_name.ilike(f"%{value}%")
        )

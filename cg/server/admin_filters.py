from flask_admin.contrib.sqla.filters import FilterLike
from flask_admin.model.filters import BaseFilter

from cg.store.models import InstrumentRun, PacbioSampleSequencingMetrics, PacbioSequencingRun


class PacbioRunNameFilter(FilterLike):
    name = "PacBio Run Name"

    def apply(self, query, value, alias=None):
        # Manually join PacbioInstrumentRun to filter only those
        return query.join(PacbioSampleSequencingMetrics.instrument_run).join(PacbioSequencingRun,
                  PacbioSequencingRun.id == InstrumentRun.id).filter(
            PacbioSequencingRun.run_name.ilike(f"%{value}%")
        )

    def operation(self):
        return "contains"
"""Store class that combines all CRUD operations for the CG database."""

from cg.store.crud.create import CreateMixin
from cg.store.crud.delete import DeleteMixin
from cg.store.crud.update import UpdateMixin


class Store(
    CreateMixin,
    DeleteMixin,
    UpdateMixin,
):
    def update_sample_reads_pacbio(self, sample_id: str) -> None:
        reads = sum(
            metric.hifi_reads
            for metric in self.get_pacbio_sample_sequencing_metrics(
                sample_id=sample_id, smrt_cell_ids=None
            )
        )
        self.set_sample_reads_pacbio(internal_id=sample_id, reads=reads)

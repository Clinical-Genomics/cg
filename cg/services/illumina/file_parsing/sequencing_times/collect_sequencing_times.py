"""Module for the sequencing time collector."""

from cg.constants.sequencing import Sequencers
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.file_parsing.sequencing_times.hiseq_2500_sequencing_times_service import (
    Hiseq2500SequencingTimesService,
)
from cg.services.illumina.file_parsing.sequencing_times.hiseq_x_sequencing_times_service import (
    HiseqXSequencingTimesService,
)
from cg.services.illumina.file_parsing.sequencing_times.novaseq_6000_sequencing_times import (
    Novaseq6000SequencingTimesService,
)
from cg.services.illumina.file_parsing.sequencing_times.novaseq_x_sequencing_times_service import (
    NovaseqXSequencingTimesService,
)
from cg.services.illumina.file_parsing.sequencing_times.sequencing_time_service import (
    SequencingTimesService,
)


class CollectSequencingTimes:
    """Class to collect sequencing times for Illumina sequencing runs."""

    @staticmethod
    def _get_sequencing_times_service(run_directory_data) -> SequencingTimesService:
        sequencer_times_services: dict = {
            Sequencers.NOVASEQX: NovaseqXSequencingTimesService,
            Sequencers.NOVASEQ: Novaseq6000SequencingTimesService,
            Sequencers.HISEQX: HiseqXSequencingTimesService,
            Sequencers.HISEQGA: Hiseq2500SequencingTimesService,
        }
        return sequencer_times_services[run_directory_data.sequencer_type]

    def get_end_time(self, run_directory_data: IlluminaRunDirectoryData):
        """Get the end time of the sequencing run."""
        times_service: SequencingTimesService = self._get_sequencing_times_service(
            run_directory_data
        )
        return times_service.get_end_time(run_directory_data=run_directory_data)

    def get_start_time(self, run_directory_data: IlluminaRunDirectoryData):
        """Get the start time of the sequencing run."""
        times_service: SequencingTimesService = self._get_sequencing_times_service(
            run_directory_data
        )
        return times_service.get_start_time(run_directory_data=run_directory_data)

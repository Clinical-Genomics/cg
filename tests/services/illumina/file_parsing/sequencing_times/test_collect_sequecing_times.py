"""Module to test the collect sequencing times class."""

import pytest

from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.file_parsing.sequencing_times.collect_sequencing_times import (
    CollectSequencingTimes,
)
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


@pytest.mark.parametrize(
    "run_dir_data, expected_times_service",
    [
        ("novaseq_x_flow_cell", NovaseqXSequencingTimesService),
        ("novaseq_6000_pre_1_5_kits_flow_cell", Novaseq6000SequencingTimesService),
        ("hiseq_x_single_index_flow_cell", HiseqXSequencingTimesService),
        ("hiseq_2500_dual_index_flow_cell", Hiseq2500SequencingTimesService),
    ],
)
def test_collect_sequencing_time_get_service(
    run_dir_data: str, expected_times_service: SequencingTimesService, request
):
    # GIVEN run directory data and a collect sequencing time class
    sequencing_time_collector = CollectSequencingTimes()
    run_dir_data: IlluminaRunDirectoryData = request.getfixturevalue(run_dir_data)

    # WHEN retrieving the time service
    time_service: SequencingTimesService = sequencing_time_collector._get_sequencing_times_service(
        run_dir_data
    )

    # THEN the correct time service is returned
    assert time_service == expected_times_service

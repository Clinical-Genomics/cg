from datetime import datetime

import pytest

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
from cg.utils.files import get_source_modified_time_stamp
from cg.utils.time import format_time_from_ctime, format_time_from_string


@pytest.fixture
def novaseq_x_sequencing_times_service() -> NovaseqXSequencingTimesService:
    return NovaseqXSequencingTimesService()


@pytest.fixture
def novaseq_x_sequencing_start_time() -> datetime:
    return format_time_from_string("2023-11-08T16:06:11.5342935+01:00")


@pytest.fixture
def novaseq_x_sequencing_end_time() -> datetime:
    return format_time_from_string("2023-11-09T15:24:13.793134+01:00")


@pytest.fixture
def novaseq_6000_sequencing_times_service() -> Novaseq6000SequencingTimesService:
    return Novaseq6000SequencingTimesService()


@pytest.fixture
def novaseq_6000_sequencing_start_time(
    novaseq_6000_pre_1_5_kits_flow_cell: IlluminaRunDirectoryData,
) -> datetime:
    return novaseq_6000_pre_1_5_kits_flow_cell.sequenced_at


@pytest.fixture
def novaseq_6000_sequencing_end_time(
    novaseq_6000_pre_1_5_kits_flow_cell: IlluminaRunDirectoryData,
) -> datetime:
    int_time: float = get_source_modified_time_stamp(
        novaseq_6000_pre_1_5_kits_flow_cell.get_sequencing_completed_path
    )
    return format_time_from_ctime(int_time)


@pytest.fixture
def hiseq_x_sequencing_times_service() -> HiseqXSequencingTimesService:
    return HiseqXSequencingTimesService()


@pytest.fixture
def hiseq_x_sequencing_start_time(
    hiseq_x_single_index_flow_cell: IlluminaRunDirectoryData,
) -> datetime:
    return hiseq_x_single_index_flow_cell.sequenced_at


@pytest.fixture
def hiseq_x_sequencing_end_time(
    hiseq_x_single_index_flow_cell: IlluminaRunDirectoryData,
) -> datetime:
    int_time: float = get_source_modified_time_stamp(
        hiseq_x_single_index_flow_cell.get_sequencing_completed_path
    )
    return format_time_from_ctime(int_time)


@pytest.fixture
def hiseq_2500_sequencing_times_service() -> Hiseq2500SequencingTimesService:
    return Hiseq2500SequencingTimesService()


@pytest.fixture
def hiseq_2500_sequencing_start_time(
    hiseq_2500_dual_index_flow_cell: IlluminaRunDirectoryData,
) -> datetime:
    return hiseq_2500_dual_index_flow_cell.sequenced_at


@pytest.fixture
def hiseq_2500_sequencing_end_time(
    hiseq_2500_dual_index_flow_cell: IlluminaRunDirectoryData,
) -> datetime:
    return hiseq_2500_dual_index_flow_cell.sequenced_at

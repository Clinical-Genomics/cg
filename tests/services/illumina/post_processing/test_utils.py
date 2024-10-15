import math
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.sequencing import FLOWCELL_Q30_THRESHOLD, Sequencers
from cg.services.illumina.data_transfer.models import (
    IlluminaSampleSequencingMetricsDTO,
)
from cg.services.illumina.post_processing.utils import (
    _add_flow_cell_name_to_fastq_file_path,
    _combine_metrics,
    _get_valid_sample_fastqs,
    _get_weighted_average,
    _is_file_path_compressed_fastq,
    _is_lane_in_fastq_file_name,
    _is_sample_id_in_directory_name,
    _is_valid_sample_fastq_file,
    combine_sample_metrics_with_undetermined,
    create_delivery_file_in_flow_cell_directory,
    get_lane_from_sample_fastq,
    get_q30_threshold,
    get_sample_fastqs_from_flow_cell,
    get_undetermined_fastqs,
    is_sample_negative_control_with_reads_in_lane,
)


@pytest.mark.parametrize(
    "reads, is_negative_control, expected_negative_control_with_reads",
    [
        (0, False, False),
        (0, True, False),
        (1, True, True),
        (1, False, False),
    ],
    ids=[
        "no_reads_no_negative_control",
        "no_reads_negative_control",
        "reads_negative_control",
        "reads_no_negative_control",
    ],
)
def test_is_sample_negative_control_with_reads_in_lane(
    mapped_metric: IlluminaSampleSequencingMetricsDTO,
    reads: int,
    is_negative_control: bool,
    expected_negative_control_with_reads: bool,
):
    # GIVEN a metric with a specific amount of reads for a sample
    mapped_metric.total_reads_in_lane = reads

    # WHEN checking if the sample is a negative control with reads in the lane
    result: bool = is_sample_negative_control_with_reads_in_lane(
        is_negative_control=is_negative_control, metric=mapped_metric
    )

    # THEN the result should be return according to the expected outcome
    assert result == expected_negative_control_with_reads


@pytest.mark.parametrize(
    "directory, expected_result",
    [
        (Path("Sample_123"), True),
        (Path("sample/123_L0002.fastq.gz"), False),
    ],
    ids=["valid_directory", "invalid_directory"],
)
def test_is_sample_id_in_directory(directory: Path, expected_result: bool):
    # GIVEN a directory and a sample internal id
    sample_internal_id: str = "123"

    # WHEN checking if the sample id is in the directory name
    is_sample_id_in_dir: bool = _is_sample_id_in_directory_name(
        directory=directory, sample_internal_id=sample_internal_id
    )

    # THEN the result should be the expected
    assert is_sample_id_in_dir == expected_result


@pytest.mark.parametrize(
    "file_path, expected_result",
    [
        (Path("sample_L0002.fastq.gz"), True),
        (Path("sample_L0002.fastq"), False),
    ],
    ids=["compressed_file", "uncompressed_file"],
)
def test_is_file_path_compressed_fastq_with_valid_file(file_path: Path, expected_result: bool):
    # GIVEN a file

    # WHEN checking if the file path is a compressed fastq file
    is_file_compressed: bool = _is_file_path_compressed_fastq(file_path)

    # THEN the result is the expected
    assert is_file_compressed == expected_result


@pytest.mark.parametrize(
    "file_path, expected_result",
    [
        (Path("sample_L0002.fastq.gz"), True),
        (Path("sample.fastq.gz"), False),
    ],
    ids=["valid_file", "invalid_file"],
)
def test_is_lane_in_fastq_file_name_with_valid_file(file_path: Path, expected_result: bool):
    # GIVEN a valid file containing lane number

    # WHEN checking if the lane number is in the fastq file name
    is_lane_in_name: bool = _is_lane_in_fastq_file_name(file_path)

    # THEN the result should be the expected
    assert is_lane_in_name == expected_result


@pytest.mark.parametrize(
    "sample_fastq, expected_result",
    [
        (Path("Sample_123/sample_L0002.fastq.gz"), True),
        (Path("L0002.fastq.gz"), False),
        (Path("Sample_123/sample.fastq.gz"), False),
        (Path("Sample_123/123_L0002.fastq"), False),
    ],
    ids=["valid_file", "no_sample_id", "no_lane", "uncompressed"],
)
def test_is_valid_sample_fastq_file(sample_fastq: Path, expected_result: bool):
    # GIVEN a fastq file and a sample internal id
    sample_internal_id = "sample"

    # WHEN checking if the sample fastq file is valid
    is_valid_fastq: bool = _is_valid_sample_fastq_file(
        sample_fastq=sample_fastq, sample_internal_id=sample_internal_id
    )

    # THEN the result should be the expected
    assert is_valid_fastq == expected_result


def test_get_valid_sample_fastqs():
    # GIVEN a list of fastq paths with one valid and one invalid path
    fastq_paths: list[Path] = [Path("Sample_123/sample_L0002.fastq.gz"), Path("L0002.fastq.gz")]

    # WHEN getting the valid fastq files
    valid_fastqs: list[Path] = _get_valid_sample_fastqs(
        fastq_paths=fastq_paths, sample_internal_id="123"
    )

    # THEN the result should be the valid fastq file
    assert len(valid_fastqs) == 1
    assert valid_fastqs[0] == Path("Sample_123/sample_L0002.fastq.gz")


@pytest.mark.parametrize(
    "demux_run_path_fixture, sample_internal_id",
    [
        ("tmp_demultiplexed_novaseq_6000_post_1_5_kits_path", "ACC12642A7"),
        ("novaseq_x_demux_runs_dir", "ACC13169A1"),
    ],
    ids=["demuxed_on_dragen", "demuxed_on_sequencer"],
)
def test_get_sample_fastqs_from_flow_cell(
    demux_run_path_fixture: str, sample_internal_id: str, request: FixtureRequest
):
    # GIVEN a demultiplexed run path and a sample internal id
    demux_run_path: Path = request.getfixturevalue(demux_run_path_fixture)

    # WHEN getting the sample fastq files from the flow cell directory
    sample_fastqs: list[Path] = get_sample_fastqs_from_flow_cell(
        demultiplexed_run_path=demux_run_path, sample_internal_id=sample_internal_id
    )

    # THEN valid sample fastq files should be returned
    assert len(sample_fastqs) == 2
    for fastq in sample_fastqs:
        assert fastq.name.startswith(sample_internal_id)
        assert fastq.name.endswith(".fastq.gz")


def test_add_flow_cell_name_to_fastq_file_path(
    tmp_path: Path,
    novaseq_6000_post_1_5_kits_fastq_file_names: list[str],
    novaseq_6000_post_1_5_kits_flow_cell_id: str,
):
    # GIVEN a list of fastq files in a tmp_path that need renaming
    result_file_paths: list[Path] = []
    for fastq_file_name in novaseq_6000_post_1_5_kits_fastq_file_names:
        fastq_file_path = Path(tmp_path, fastq_file_name)
        fastq_file_path.touch()

        # WHEN adding the flow cell name to the fastq file path
        result_file_paths.append(
            _add_flow_cell_name_to_fastq_file_path(
                fastq_file_path=fastq_file_path,
                flow_cell_id=novaseq_6000_post_1_5_kits_flow_cell_id,
            )
        )

    # THEN all the fastq files should have the flow cell id in their names
    assert (
        file.name.startswith(novaseq_6000_post_1_5_kits_flow_cell_id) for file in result_file_paths
    )


@pytest.mark.parametrize(
    "total_1, percentage_1, total_2, percentage_2, expected_result",
    [
        (50, 0.9, 50, 0.7, 0.8),
        (0, 0.0, 0, 0.0, 0.0),
    ],
    ids=["equal_totals", "zero_counts"],
)
def test_get_weighted_average(
    total_1: int, percentage_1: float, total_2: int, percentage_2: float, expected_result: float
):
    # GIVEN total counts and percentages for two metrics

    # WHEN Calculating the weighted average
    result: float = _get_weighted_average(
        total_1=total_1, percentage_1=percentage_1, total_2=total_2, percentage_2=percentage_2
    )

    # THEN The weighted average should be 0.8
    assert math.isclose(result, expected_result, rel_tol=1e-9)


def test_combine_metrics(
    mapped_metric: IlluminaSampleSequencingMetricsDTO,
    undetermined_metric: IlluminaSampleSequencingMetricsDTO,
):
    # GIVEN two metrics

    # WHEN Combining the metrics
    existing_metric: IlluminaSampleSequencingMetricsDTO = _combine_metrics(
        existing_metric=mapped_metric, new_metric=undetermined_metric
    )

    # THEN The existing metric should be updated
    assert existing_metric.total_reads_in_lane == 200
    assert existing_metric.yield_ == 200


@pytest.mark.parametrize(
    "mapped_metrics, undetermined_metrics, expected_result",
    [
        ([], [], []),
        (["mapped_metric"], [], ["mapped_metric"]),
        ([], ["undetermined_metric"], ["undetermined_metric"]),
        (["mapped_metric"], ["undetermined_metric"], ["combined_metric"]),
    ],
    ids=["empty", "only_mapped", "only_undetermined", "both_mapped_and_undetermined"],
)
def test_combine_metrics(
    mapped_metrics: list[str | None],
    undetermined_metrics: list[str | None],
    expected_result: list[str | None],
    request: FixtureRequest,
):
    # GIVEN a combination of mapped and undetermined metrics
    mapped_metrics: list[IlluminaSampleSequencingMetricsDTO | None] = [
        request.getfixturevalue(fixture_name) for fixture_name in mapped_metrics
    ]
    undetermined_metrics: list[IlluminaSampleSequencingMetricsDTO | None] = [
        request.getfixturevalue(fixture_name) for fixture_name in undetermined_metrics
    ]

    # WHEN combining the metrics
    combined_metrics: list[IlluminaSampleSequencingMetricsDTO | None] = (
        combine_sample_metrics_with_undetermined(
            sample_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
        )
    )

    # THEN the combined metrics should be as expected
    expected_metrics: list[IlluminaSampleSequencingMetricsDTO | None] = [
        request.getfixturevalue(fixture_name) for fixture_name in expected_result
    ]
    assert combined_metrics == expected_metrics


def test_combine_metrics_with_both_mapped_and_undetermined_metrics_different_lanes(
    mapped_metric: IlluminaSampleSequencingMetricsDTO,
    undetermined_metric: IlluminaSampleSequencingMetricsDTO,
):
    # GIVEN one mapped and one undetermined metric in different lanes for a sample
    mapped_metrics = [mapped_metric]
    undetermined_metric.flow_cell_lane = 2
    undetermined_metrics = [undetermined_metric]

    # WHEN combining them
    combined_metrics = combine_sample_metrics_with_undetermined(
        sample_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
    )

    # THEN two metrics should be returned
    assert len(combined_metrics) == 2
    assert combined_metrics[0].flow_cell_lane != combined_metrics[1].flow_cell_lane


def test_get_undetermined_fastqs(tmp_demultiplexed_novaseq_6000_post_1_5_kits_path: Path):
    # GIVEN a demultiplexed run with undetermined fastq files

    # WHEN getting the undetermined fastq files
    undetermined_fastqs: list[Path] = get_undetermined_fastqs(
        lane=1, demultiplexed_run_path=tmp_demultiplexed_novaseq_6000_post_1_5_kits_path
    )

    # THEN the result should be the undetermined fastq file
    assert len(undetermined_fastqs) == 2
    assert all(
        undetermined_fastq.name.startswith("Undetermined")
        for undetermined_fastq in undetermined_fastqs
    )


def test_create_delivery_file_in_flow_cell_directory(tmp_path: Path):
    # GIVEN a temporary directory without a delivery file
    flow_cell_directory: Path = tmp_path
    assert not (flow_cell_directory / DemultiplexingDirsAndFiles.DELIVERY).exists()

    # WHEN creating a delivery file inside the temporary directory
    create_delivery_file_in_flow_cell_directory(flow_cell_directory)

    # THEN a delivery file should exist in the temporary directory
    assert (flow_cell_directory / DemultiplexingDirsAndFiles.DELIVERY).exists()


@pytest.mark.parametrize(
    "sample_fastq_file_name",
    [
        "novaseq_6000_post_1_5_kits_fastq_file_lane_1",
        "novaseq_6000_post_1_5_kits_fastq_file_lane_1_with_flow_cell_id",
    ],
    ids=["no_flow_cell_id", "with_flow_cell_id"],
)
def test_get_lane_from_sample_fastq_file_path(sample_fastq_file_name: str, request: FixtureRequest):
    # GIVEN a sample fastq path and a lane
    fastq_file: str = request.getfixturevalue(sample_fastq_file_name)
    sample_fastq_path = Path(fastq_file)
    expected_lane: int = 1

    # WHEN we get lane from the sample fastq file path
    result_lane: int = get_lane_from_sample_fastq(sample_fastq_path)

    # THEN we should get the correct lane
    assert result_lane == expected_lane


def test_get_q30_threshold():
    # GIVEN a specific sequencer type
    sequencer_type: Sequencers = Sequencers.HISEQGA

    # WHEN getting the Q30 threshold for the sequencer type
    q30_threshold: int = get_q30_threshold(sequencer_type)

    # THEN the correct Q30 threshold should be returned
    assert q30_threshold == FLOWCELL_Q30_THRESHOLD[sequencer_type]

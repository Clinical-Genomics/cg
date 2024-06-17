import math
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.services.illumina_services.illumina_metrics_service.models import (
    IlluminaSampleSequencingMetricsDTO,
)
from cg.services.illumina_services.illumina_post_processing_service.utils import (
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
)


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


def test_combine_empty_metrics():
    # GIVEN empty lists for mapped and undetermined metrics
    mapped_metrics = []
    undetermined_metrics = []

    # WHEN combining them
    combined_metrics = combine_sample_metrics_with_undetermined(
        sample_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
    )

    # THEN the result should be an empty list
    assert combined_metrics == []


def test_combine_metrics_with_only_mapped_metrics(
    mapped_metric: IlluminaSampleSequencingMetricsDTO,
):
    # GIVEN one mapped metric and no undetermined
    mapped_metrics = [mapped_metric]
    undetermined_metrics = []

    # WHEN combining them
    combined_metrics = combine_sample_metrics_with_undetermined(
        sample_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
    )

    # THEN the result should be the mapped metrics
    assert combined_metrics == mapped_metrics


def test_combine_metrics_with_only_undetermined_metrics(
    undetermined_metric: IlluminaSampleSequencingMetricsDTO,
):
    # GIVEN an empty list of mapped metrics and list of undetermined metrics
    mapped_metrics = []
    undetermined_metrics = [undetermined_metric]

    # WHEN combining them
    combined_metrics = combine_sample_metrics_with_undetermined(
        sample_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
    )

    # THEN the result should be the undetermined metrics
    assert combined_metrics == undetermined_metrics


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


def test_combine_metrics_with_both_mapped_and_undetermined_metrics_same_lane(
    mapped_metric: IlluminaSampleSequencingMetricsDTO,
    undetermined_metric: IlluminaSampleSequencingMetricsDTO,
):
    # GIVEN a list of mapped metrics and list of undetermined metrics in the same lane for the same sample

    # WHEN combining them
    combined_metrics = combine_sample_metrics_with_undetermined(
        sample_metrics=[mapped_metric], undetermined_metrics=[undetermined_metric]
    )

    # THEN the combined metrics should be a single metric
    assert len(combined_metrics) == 1

    # THEN the metrics should be a weighted average of the mapped and undetermined metrics
    metric: IlluminaSampleSequencingMetricsDTO = combined_metrics[0]
    assert metric.total_reads_in_lane == 200
    assert metric.yield_ == 200
    assert math.isclose(metric.yield_q30, 0.85, rel_tol=1e-9)
    assert math.isclose(metric.base_passing_q30_percent, 0.85, rel_tol=1e-9)
    assert metric.base_mean_quality_score == 25


def test_validate_demux_complete_flow_cell_directory_when_it_exists(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory with a demux complete file
    flow_cell_directory: Path = tmp_path
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).touch()

    # WHEN the create_delivery_file_in_flow_cell_directory function is called
    create_delivery_file_in_flow_cell_directory(flow_cell_directory)

    # THEN a delivery file should exist in the flow cell directory
    assert (flow_cell_directory / DemultiplexingDirsAndFiles.DEMUX_COMPLETE).exists()


def test_validate_demux_complete_flow_cell_directory_when_it_does_not_exist(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory without a demux complete file
    flow_cell_directory: Path = tmp_path

    # WHEN the create_delivery_file_in_flow_cell_directory function is called
    create_delivery_file_in_flow_cell_directory(flow_cell_directory)

    # THEN a delivery file should not exist in the flow cell directory
    assert not (flow_cell_directory / DemultiplexingDirsAndFiles.DEMUX_COMPLETE).exists()


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

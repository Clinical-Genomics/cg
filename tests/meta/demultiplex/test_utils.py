from pathlib import Path

import pytest

from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.sequencing import FLOWCELL_Q30_THRESHOLD, Sequencers
from cg.exc import FlowCellError
from cg.io.csv import read_csv
from cg.meta.demultiplex.utils import (
    NANOPORE_SEQUENCING_SUMMARY_PATTERN,
    add_flow_cell_name_to_fastq_file_path,
    are_all_files_synced,
    create_delivery_file_in_flow_cell_directory,
    create_manifest_file,
    get_existing_manifest_file,
    get_lane_from_sample_fastq,
    get_nanopore_summary_file,
    get_q30_threshold,
    get_sample_sheet_path_from_flow_cell_dir,
    get_undetermined_fastqs,
    is_file_path_compressed_fastq,
    is_file_relevant_for_demultiplexing,
    is_flow_cell_sync_confirmed,
    is_lane_in_fastq_file_name,
    is_manifest_file_required,
    is_nanopore_sequencing_complete,
    is_sample_id_in_directory_name,
    is_syncing_complete,
    is_valid_sample_fastq_file,
    parse_manifest_file,
)
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from tests.meta.demultiplex.conftest import get_all_files_in_directory_tree


def test_validate_sample_fastq_with_valid_file():
    # GIVEN a sample fastq file with a lane number and sample id in the parent directory name
    sample_fastq = Path("Sample_123/sample_L0002.fastq.gz")

    # WHEN validating the sample fastq file
    is_valid_fastq: bool = is_valid_sample_fastq_file(
        sample_fastq=sample_fastq, sample_internal_id="sample"
    )

    # THEN it should be valid
    assert is_valid_fastq


def test_validate_sample_fastq_without_sample_id_in_parent_directory_name():
    # GIVEN a sample fastq file without a sample id in the parent directory name or file name
    sample_fastq = Path("L0002.fastq.gz")

    # WHEN validating the sample fastq file
    is_valid_fastq: bool = is_valid_sample_fastq_file(
        sample_fastq=sample_fastq, sample_internal_id="sample_id"
    )

    # THEN it should not be valid
    assert not is_valid_fastq


def test_validate_sample_fastq_without_lane_number_in_path():
    # GIVEN a sample fastq file without a lane number
    sample_fastq = Path("Sample_123/sample_id.fastq.gz")

    # WHEN validating the sample fastq file
    is_valid_fastq: bool = is_valid_sample_fastq_file(sample_fastq, sample_internal_id="sample_id")

    # THEN it should not be valid
    assert not is_valid_fastq


def test_validate_sample_fastq_with_invalid_file_extension():
    # GIVEN a sample fastq file without a valid file extension
    sample_fastq = Path("Sample_123/123_L0002.fastq")

    # WHEN validating the sample fastq file
    is_valid_fastq: bool = is_valid_sample_fastq_file(sample_fastq, sample_internal_id="123")

    # THEN it should not be valid
    assert not is_valid_fastq


def test_is_file_path_compressed_fastq_with_valid_file():
    # GIVEN a valid .fastq.gz file
    file_path = Path("sample_L0002.fastq.gz")

    # WHEN checking if the file path is a compressed fastq file
    is_file_compressed: bool = is_file_path_compressed_fastq(file_path)

    # THEN the result should be True
    assert is_file_compressed


def test_is_file_path_compressed_fastq_with_invalid_file():
    # GIVEN a file with invalid extension
    file_path = Path("sample_L0002.fastq")

    # WHEN checking if the file path is a compressed fastq file
    is_file_compressed: bool = is_file_path_compressed_fastq(file_path)

    # THEN the result should be False
    assert not is_file_compressed


def test_is_lane_in_fastq_file_name_with_valid_file():
    # GIVEN a valid file containing lane number
    file_path = Path("sample_L0002.fastq.gz")

    # WHEN checking if the lane number is in the fastq file name
    is_lane_in_name: bool = is_lane_in_fastq_file_name(file_path)

    # THEN the result should be True
    assert is_lane_in_name


def test_is_lane_in_fastq_file_name_with_invalid_file():
    # GIVEN a file without lane number
    file_path = Path("sample.fastq.gz")

    # WHEN checking if the lane number is in the fastq file name
    is_lane_in_name: bool = is_lane_in_fastq_file_name(file_path)

    # THEN the result should be False
    assert not is_lane_in_name


def test_is_sample_id_in_directory_name_with_valid_directory():
    # GIVEN a directory containing sample id
    directory = Path("Sample_123")

    # WHEN checking if the sample id is in the directory name
    is_sample_id_in_dir: bool = is_sample_id_in_directory_name(
        directory=directory, sample_internal_id="123"
    )

    # THEN the result should be True
    assert is_sample_id_in_dir


def test_is_sample_id_in_directory_name_with_invalid_directory():
    # GIVEN a directory without sample id
    directory = Path("sample/123_L0002.fastq.gz")

    # WHEN checking if the sample id is in the directory name
    is_sample_id_in_dir: bool = is_sample_id_in_directory_name(
        directory=directory, sample_internal_id="sample_id"
    )

    # THEN the result should be False
    assert is_sample_id_in_dir is False


def test_get_lane_from_sample_fastq_file_path():
    # GIVEN a sample fastq path
    initial_lane: int = 4
    sample_fastq_path = Path(
        f"H5CYFDSX7_ACC12164A17_S367_L00{initial_lane}"
        f"_R1_001{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    )

    # WHEN we get lane from the sample fastq file path
    result_lane: int = get_lane_from_sample_fastq(sample_fastq_path)

    # THEN we should get the correct lane
    assert result_lane == initial_lane


def test_get_lane_from_sample_fastq_file_path_no_flowcell():
    # GIVEN a sample fastq path without a flow cell id
    initial_lane: int = 4
    sample_fastq_path = Path(
        f"ACC12164A17_S367_L00{initial_lane}_R1_001{FileExtensions.FASTQ}{FileExtensions.GZIP}",
    )

    # WHEN we get lane from the sample fastq file path
    result_lane: int = get_lane_from_sample_fastq(sample_fastq_path)

    # THEN we should get the correct lane
    assert result_lane == initial_lane


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


def test_get_q30_threshold():
    # GIVEN a specific sequencer type
    sequencer_type: Sequencers = Sequencers.HISEQGA

    # WHEN getting the Q30 threshold for the sequencer type
    q30_threshold: int = get_q30_threshold(sequencer_type)

    # THEN the correct Q30 threshold should be returned
    assert q30_threshold == FLOWCELL_Q30_THRESHOLD[sequencer_type]


def test_get_sample_sheet_path_found(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory
    flow_cell_directory: Path = tmp_path

    # GIVEN a sample sheet file in the flow cell directory
    sample_sheet_path = Path(flow_cell_directory, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)
    sample_sheet_path.touch()

    # WHEN the sample sheet is retrieved
    found_sample_sheet_path: Path = get_sample_sheet_path_from_flow_cell_dir(flow_cell_directory)

    # THEN the path to the sample sheet file should be returned
    assert found_sample_sheet_path == sample_sheet_path


def test_get_sample_sheet_path_found_in_nested_directory(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory
    flow_cell_directory: Path = tmp_path

    # GIVEN a nested directory within the flow cell directory
    nested_directory = Path(flow_cell_directory, "nested")
    nested_directory.mkdir()

    # GIVEN a sample sheet file in the nested directory
    sample_sheet_path = Path(nested_directory, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)
    sample_sheet_path.touch()

    # WHEN the sample sheet is retrieved
    found_sample_sheet_path: Path = get_sample_sheet_path_from_flow_cell_dir(flow_cell_directory)

    # THEN the path to the sample sheet file should be returned
    assert found_sample_sheet_path == sample_sheet_path


def test_get_sample_sheet_path_not_found(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory without a sample sheet file
    flow_cell_directory: Path = tmp_path

    # WHEN the sample sheet is retrieved
    # THEN a FileNotFoundError should be raised
    with pytest.raises(FileNotFoundError):
        get_sample_sheet_path_from_flow_cell_dir(flow_cell_directory)


def test_parse_flow_cell_directory_data_invalid():
    """Test that a FlowCellDirectoryData object is not created when the given path is invalid."""
    with pytest.raises(FlowCellError):
        IlluminaRunDirectoryData(Path("invalid_path"))


def test_parse_flow_cell_directory_data_valid(novaseq_6000_post_1_5_kits_flow_cell_full_name: str):
    # GIVEN a flow cell directory which is valid

    # WHEN parsing the flow cell directory data
    result = IlluminaRunDirectoryData(Path(novaseq_6000_post_1_5_kits_flow_cell_full_name))

    # THEN a FlowCellDirectoryData object should be returned
    assert isinstance(result, IlluminaRunDirectoryData)

    # THEN the flow cell path and bcl converter should be set
    assert result.path == Path(novaseq_6000_post_1_5_kits_flow_cell_full_name)


def test_parse_manifest_file(novaseq_x_manifest_file: Path):
    # GIVEN a manifest file

    # WHEN parsing the manifest file
    files_at_source: list[Path] = parse_manifest_file(novaseq_x_manifest_file)

    # THEN paths should be returned
    # THEN the paths should be Path objects
    assert files_at_source
    assert isinstance(files_at_source, list)
    assert all(isinstance(file, Path) for file in files_at_source)


@pytest.mark.parametrize(
    "file, expected_result",
    [
        (Path("flow_cell_dir", DemultiplexingDirsAndFiles.DATA, "some_file.txt"), True),
        (Path("flow_cell_dir", DemultiplexingDirsAndFiles.INTER_OP, "some_file.txt"), True),
        (Path("flow_cell_dir", "Thumbnail_Images", "some_file.txt"), False),
    ],
)
def test_is_file_relevant_for_demultiplexing(file: Path, expected_result: bool):
    # GIVEN a file path

    # WHEN checking if the file is relevant
    result = is_file_relevant_for_demultiplexing(file)

    # THEN the correct result should be returned
    assert result == expected_result


def test_get_existing_manifest_file_illumina(lsyncd_source_directory: Path):
    # GIVEN a directory with an Illumina manifest file

    # WHEN getting the manifest file
    manifest_file: Path = get_existing_manifest_file(lsyncd_source_directory)

    # THEN the manifest file should be returned
    assert manifest_file == Path(
        lsyncd_source_directory, DemultiplexingDirsAndFiles.ILLUMINA_FILE_MANIFEST
    )


def test_get_existing_manifest_file(lsyncd_source_directory: Path):
    # GIVEN a directory with a custom manifest file
    Path(lsyncd_source_directory, DemultiplexingDirsAndFiles.ILLUMINA_FILE_MANIFEST).rename(
        Path(lsyncd_source_directory, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST)
    )

    # WHEN getting the manifest file
    manifest_file: Path = get_existing_manifest_file(lsyncd_source_directory)

    # THEN the manifest file should be returned
    assert manifest_file == Path(
        lsyncd_source_directory, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST
    )


def test_get_existing_manifest_file_missing(lsyncd_source_directory: Path):
    # GIVEN a directory with a missing manifest file
    Path(lsyncd_source_directory, DemultiplexingDirsAndFiles.ILLUMINA_FILE_MANIFEST).unlink()

    # WHEN getting the manifest file
    manifest_file: Path = get_existing_manifest_file(lsyncd_source_directory)

    # THEN the manifest file should be returned
    assert manifest_file is None


def test_is_syncing_complete_true(lsyncd_source_directory: Path, lsyncd_target_directory: Path):
    # GIVEN a source directory with a manifest file

    # GIVEN a target directory with all relevant files

    # WHEN checking if the syncing is complete
    is_directory_synced: bool = is_syncing_complete(
        source_directory=lsyncd_source_directory, target_directory=lsyncd_target_directory
    )

    # THEN the syncing should be deemed complete
    assert is_directory_synced


def test_are_all_files_synced_false(
    novaseq_x_manifest_file: Path, lsyncd_source_directory: Path, lsyncd_target_directory: Path
):
    # GIVEN a source directory with a manifest file
    files_at_source: list[Path] = parse_manifest_file(novaseq_x_manifest_file)

    # GIVEN a target directory with one file missing
    Path(lsyncd_target_directory, files_at_source[0]).unlink()

    # WHEN checking if the syncing is complete
    is_directory_synced: bool = are_all_files_synced(
        files_at_source=files_at_source, target_directory=lsyncd_target_directory
    )

    # THEN the syncing should not be deemed complete
    assert not is_directory_synced


def test_are_all_files_synced(
    novaseq_x_manifest_file: Path, lsyncd_source_directory: Path, lsyncd_target_directory: Path
):
    # GIVEN a source directory with a manifest file
    files_at_source: list[Path] = parse_manifest_file(novaseq_x_manifest_file)

    # GIVEN a target directory with all relevant files

    # WHEN checking if the syncing is complete
    is_directory_synced: bool = are_all_files_synced(
        files_at_source=files_at_source, target_directory=lsyncd_target_directory
    )

    # THEN the syncing should be deemed complete
    assert is_directory_synced


def test_is_syncing_complete_false(
    lsyncd_source_directory: Path, lsyncd_target_directory: Path, base_call_file: Path
):
    """Tests if the syncing is not complete when a file is missing."""
    # GIVEN a source directory with a manifest file

    # GIVEN a target directory without all relevant files
    Path(lsyncd_target_directory, base_call_file).unlink()

    # WHEN checking if the syncing is complete
    is_directory_synced: bool = is_syncing_complete(
        source_directory=lsyncd_source_directory, target_directory=lsyncd_target_directory
    )

    # THEN the syncing should not be deemed complete
    assert not is_directory_synced


@pytest.mark.parametrize(
    "source_files, expected_result",
    [
        ([DemultiplexingDirsAndFiles.COPY_COMPLETE], True),
        ([DemultiplexingDirsAndFiles.ILLUMINA_FILE_MANIFEST], False),
        (
            [
                DemultiplexingDirsAndFiles.ILLUMINA_FILE_MANIFEST,
                DemultiplexingDirsAndFiles.COPY_COMPLETE,
            ],
            False,
        ),
        ([DemultiplexingDirsAndFiles.CG_FILE_MANIFEST], False),
        (
            [
                DemultiplexingDirsAndFiles.CG_FILE_MANIFEST,
                DemultiplexingDirsAndFiles.COPY_COMPLETE,
            ],
            False,
        ),
        ([NANOPORE_SEQUENCING_SUMMARY_PATTERN.replace("*", "FlowCell_ID1_ID2")], True),
    ],
)
def test_is_manifest_file_required(source_files: list[str], expected_result: bool, tmp_path: Path):
    """Tests if a manifest file is needed given the files present."""
    # GIVEN a source directory
    source_directory = Path(tmp_path, "source")
    Path(tmp_path, "source").mkdir()

    # GIVEN the files present
    for file in source_files:
        Path(source_directory, file).touch()

    # WHEN checking if a manifest file is needed
    is_required = is_manifest_file_required(source_directory)

    # THEN the result should as expected
    assert is_required == expected_result


def test_is_manifest_file_required_nanopore_data(tmp_path: Path):
    """Tests if a manifest file is needed given the files present."""
    # GIVEN a source directory
    source_directory = Path(tmp_path, "source")
    Path(tmp_path, "source").mkdir()

    # WHEN checking if a manifest file is needed
    is_required = is_manifest_file_required(source_directory)

    # THEN the result should as expected
    assert is_required is False


@pytest.mark.parametrize(
    "source_files, expected_result",
    [([DemultiplexingDirsAndFiles.COPY_COMPLETE], True), ([], False)],
)
def test_is_flow_cell_sync_confirmed(
    source_files: list[str], expected_result: bool, tmp_path: Path
):
    """Tests that a flow cell sync has been confirmed."""
    # GIVEN a flow cell directory with the given file present
    for file in source_files:
        Path(tmp_path, file).touch()

    # WHEN checking if the flow cell sync has been confirmed
    is_synced = is_flow_cell_sync_confirmed(tmp_path)

    # THEN the result should match what we expect
    assert is_synced == expected_result


def test_create_manifest_file(tmp_flow_cells_directory_ready_for_demultiplexing: Path):
    # GIVEN a flow cell directory with files
    all_files: list[Path] = get_all_files_in_directory_tree(
        tmp_flow_cells_directory_ready_for_demultiplexing
    )
    # WHEN creating a manifest file
    manifest_file: Path = create_manifest_file(tmp_flow_cells_directory_ready_for_demultiplexing)

    # THEN a manifest file should be created
    assert manifest_file.exists()

    # Then all files should be included in the manifest_file
    assert_file_contains_all_file_paths(manifest_file=manifest_file, files_in_file=all_files)


def assert_file_contains_all_file_paths(manifest_file: Path, files_in_file: list[Path]):
    """Asserts that all files in files_in_file are present in the manifest_file."""
    files_in_manifest: list[Path] = [
        Path(file[0].strip()) for file in read_csv(delimiter="\t", file_path=manifest_file)
    ]
    for manifest_file in files_in_file:
        assert manifest_file in files_in_manifest


def test_add_flow_cell_name_to_fastq_file_path(
    hiseq_x_single_index_flow_cell_id: str, demultiplex_fastq_file_path
):
    # GIVEN a fastq file path and a flow cell name

    # WHEN adding the flow cell name to the fastq file path
    rename_fastq_file_path: Path = add_flow_cell_name_to_fastq_file_path(
        fastq_file_path=demultiplex_fastq_file_path,
        flow_cell_name=hiseq_x_single_index_flow_cell_id,
    )

    # THEN the fastq file path should be returned with the flow cell name added
    assert rename_fastq_file_path == Path(
        demultiplex_fastq_file_path.parent,
        f"{hiseq_x_single_index_flow_cell_id}_{demultiplex_fastq_file_path.name}",
    )


def test_add_flow_cell_name_to_fastq_file_path_when_flow_cell_name_already_in_name(
    novaseq_6000_pre_1_5_kits_flow_cell_id: str, demultiplex_fastq_file_path
):
    # GIVEN a fastq file path and a flow cell name

    # GIVEN that the flow cell name is already in the fastq file path
    demultiplex_fastq_file_path = Path(
        f"{novaseq_6000_pre_1_5_kits_flow_cell_id}_{demultiplex_fastq_file_path.name}"
    )

    # WHEN adding the flow cell name to the fastq file path
    renamed_fastq_file_path: Path = add_flow_cell_name_to_fastq_file_path(
        fastq_file_path=demultiplex_fastq_file_path,
        flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id,
    )

    # THEN the fastq file path should be returned equal to the original fastq file path
    assert renamed_fastq_file_path == demultiplex_fastq_file_path


def test_get_undetermined_fastqs_no_matching_files(tmp_path):
    # GIVEN a lane and a flow cell with no undetermined fastq files

    # WHEN reetrieving undetermined fastqs for the lane
    result = get_undetermined_fastqs(lane=1, flow_cell_path=tmp_path)

    # THEN no undetermined fastq files should be returned
    assert not result


def test_get_undetermined_fastqs_single_matching_file(tmp_path):
    # GIVEN a flow cell with one undetermined fastq file
    expected_file: Path = Path(tmp_path, "Undetermined_L001_R1.fastq.gz")
    expected_file.touch()

    # WHEN retrieving undetermined fastqs for the lane
    result = get_undetermined_fastqs(lane=1, flow_cell_path=tmp_path)

    # THEN the undetermined fastq file for the lane should be returned
    assert result == [expected_file]


def test_get_undetermined_fastqs_multiple_matching_files(tmp_path):
    # GIVEN a flow cell with multiple undetermined fastq files for a lane
    expected_files = [
        Path(tmp_path, "Undetermined_L001_R1.fastq.gz"),
        Path(tmp_path, "Undetermined_L001_R2.fastq.gz"),
    ]
    for file in expected_files:
        file.touch()

    # WHEN retrieving the undetermined fastqs for the lane
    result = get_undetermined_fastqs(lane=1, flow_cell_path=tmp_path)

    # THEN the undetermined fastq files for the lane should be returned
    assert set(result) == set(expected_files)


def test_get_nanopore_summary_file_exists(tmp_path: Path):
    # GIVEN a directory with a correct file in it
    file_in_directory = Path(tmp_path, "final_summary_some_flow_cell.txt")
    file_in_directory.touch()

    # WHEN getting the nanopore summary file
    file: Path | None = get_nanopore_summary_file(tmp_path)

    # THEN the final summary file should be returned
    assert file == file_in_directory


def test_get_nanopore_summary_file(tmp_path: Path):
    # GIVEN a directory without a summary file in it
    file_in_directory = Path(tmp_path, "not_a_summary_file.txt")
    file_in_directory.touch()

    # WHEN getting the nanopore summary file
    file: Path | None = get_nanopore_summary_file(tmp_path)

    # THEN None should be returned
    assert file is None


def test_is_nanopore_sequencing_complete(tmp_path: Path):
    # GIVEN a directory with a correct file in it
    file_in_directory = Path(tmp_path, "final_summary_some_flow_cell.txt")
    file_in_directory.touch()

    # WHEN checking if the sequencing is complete
    is_complete: bool = is_nanopore_sequencing_complete(tmp_path)

    # THEN the sequencing should be complete
    assert is_complete


def test_is_nanopore_sequencing_incomplete(tmp_path: Path):
    # GIVEN a directory with no file in it

    # WHEN checking if the sequencing is complete
    is_complete: bool = is_nanopore_sequencing_complete(tmp_path)

    # THEN the sequencing should be complete
    assert not is_complete

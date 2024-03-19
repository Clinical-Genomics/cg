"""Test how the api handles files."""

from datetime import datetime
from pathlib import Path
from typing import Any

from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from tests.meta.compress.conftest import MockCompressionData
from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.small_helpers import SmallHelpers
from tests.store_helpers import StoreHelpers


def test_new_file(bed_file: Path, housekeeper_api: MockHousekeeperAPI, small_helpers: SmallHelpers):
    """Test to create a new file with the Housekeeper API"""
    # GIVEN a housekeeper api without files and the path to an existing file
    assert small_helpers.length_of_iterable(housekeeper_api.files()) == 0
    assert bed_file.exists() is True

    # WHEN creating a new file
    new_file = housekeeper_api.new_file(path=bed_file.as_posix())

    # THEN assert a file object was created
    assert new_file

    # THEN assert that the path is correct
    assert new_file.path == bed_file.as_posix()

    # THEN assert that no file is added to the database
    assert small_helpers.length_of_iterable(housekeeper_api.files()) == 0


def test_new_file_non_existing_path(housekeeper_api: MockHousekeeperAPI):
    """Test to create a new file with the Housekeeper API."""
    # GIVEN a housekeeper api without files and the path to a not existing file
    file_name = Path("a_file.hello")
    assert file_name.exists() is False

    # WHEN creating a new file
    new_file: File = housekeeper_api.new_file(path=file_name.as_posix())

    # THEN assert a file object was created
    assert new_file

    # THEN assert that the path is correct
    assert new_file.path == file_name.as_posix()


def test_add_new_file(
    populated_housekeeper_api: MockHousekeeperAPI,
    case_id: str,
    madeline_output: Path,
    small_helpers: SmallHelpers,
    not_existing_hk_tag: str,
):
    """Test to create a new file with the Housekeeper API."""
    # GIVEN a populated housekeeper api and the existing version of a bundle
    version: Version = populated_housekeeper_api.last_version(bundle=case_id)

    # GIVEN an existing file that is not included in the database
    assert madeline_output.exists() is True

    # GIVEN a tag that does not exist
    assert populated_housekeeper_api.get_tag(name=not_existing_hk_tag) is None

    # GIVEN a known number of files in the db
    nr_files_in_db = small_helpers.length_of_iterable(populated_housekeeper_api.files())

    # WHEN creating a new file
    new_file: File = populated_housekeeper_api.add_file(
        path=madeline_output, version_obj=version, tags=not_existing_hk_tag
    )

    # THEN assert a file object was created
    assert new_file

    # THEN assert that the path is correct
    assert new_file.path == madeline_output.resolve().as_posix()

    # THEN assert that the file was not added to the database
    new_nr_files = small_helpers.length_of_iterable(populated_housekeeper_api.files())
    assert new_nr_files == nr_files_in_db + 1


def test_get_file(populated_housekeeper_api: HousekeeperAPI):
    """Test to get a file from the database."""
    # GIVEN a housekeeper api with a file
    hk_file: File = populated_housekeeper_api.files().first()

    # GIVEN the id of a file that exists in HK
    assert hk_file

    # WHEN fetching the file with get_file
    hk_file = populated_housekeeper_api.get_file(hk_file.id)

    # THEN assert a file was returned
    assert hk_file is not None


def test_get_files_from_version(
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
    hk_bundle_data: dict[str, Any],
    hk_tag: str,
    observations_clinical_snv_file_path: Path,
    observations_clinical_sv_file_path: Path,
):
    """Test get the files from the Housekeeper database given the version object."""

    # GIVEN a Housekeeper API with some files
    version: Version = helpers.ensure_hk_version(real_housekeeper_api, hk_bundle_data)
    first_file: File = real_housekeeper_api.add_file(
        path=observations_clinical_snv_file_path, version_obj=version, tags=hk_tag
    )
    second_file: File = real_housekeeper_api.add_file(
        path=observations_clinical_sv_file_path, version_obj=version, tags=hk_tag
    )

    # GIVEN that the files exist in the version object
    assert first_file in version.files
    assert second_file in version.files

    # WHEN extracting the files from version
    files: list[File] = real_housekeeper_api.get_files_from_version(version=version, tags={hk_tag})

    # THEN the added files should be retrieved
    assert first_file in files
    assert second_file in files


def test_get_latest_file_from_version(
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
    hk_bundle_data: dict[str, Any],
    hk_tag: str,
    observations_clinical_snv_file_path: Path,
    observations_clinical_sv_file_path: Path,
):
    """Test to get the latest file from the Housekeeper database given the version object."""

    # GIVEN a Housekeeper API with some files
    version: Version = helpers.ensure_hk_version(real_housekeeper_api, hk_bundle_data)
    first_file: File = real_housekeeper_api.add_file(
        path=observations_clinical_snv_file_path, version_obj=version, tags=hk_tag
    )
    second_file: File = real_housekeeper_api.add_file(
        path=observations_clinical_sv_file_path, version_obj=version, tags=hk_tag
    )

    # GIVEN that the files exist in the version object
    assert first_file in version.files
    assert second_file in version.files

    # WHEN extracting the latest file from version
    latest_file: File = real_housekeeper_api.get_latest_file_from_version(
        version=version, tags={hk_tag}
    )

    # THEN the file with the higher ID should be returned
    assert latest_file == second_file


def test_get_file_from_latest_version(case_id: str, populated_housekeeper_api: HousekeeperAPI):
    """Test to get a file from the database from the latest version."""
    # GIVEN a housekeeper api with a file
    hk_file: File = populated_housekeeper_api.files().first()

    # GIVEN a tag of a file that exists in HK
    assert hk_file.tags

    # WHEN fetching the file
    hk_file: File = populated_housekeeper_api.get_file_from_latest_version(
        bundle_name=case_id, tags=[hk_file.tags[0].name]
    )

    # THEN assert a file was returned
    assert hk_file is not None


def test_get_files_from_latest_version(
    case_id: str, populated_housekeeper_api: HousekeeperAPI, small_helpers: SmallHelpers
):
    """Test to get files from the database from the latest version."""

    # GIVEN a Housekeeper version
    version: Version = populated_housekeeper_api.last_version(bundle=case_id)

    # GIVEN a housekeeper api with a file
    hk_file: File = populated_housekeeper_api.files().first()

    # GIVEN a tag of a file that exists in HK
    assert hk_file.tags

    # GIVEN another file with the same tag
    populated_housekeeper_api.add_file(
        path=Path("a_new_file.bed").as_posix(), tags=[hk_file.tags[0].name], version_obj=version
    )

    # WHEN fetching the files
    hk_files: list[File] = populated_housekeeper_api.get_files_from_latest_version(
        bundle_name=case_id, tags=[hk_file.tags[0].name]
    )

    # THEN assert 2 files were returned
    assert small_helpers.length_of_iterable(hk_files) == 2


def test_delete_file(populated_housekeeper_api: HousekeeperAPI):
    """Test to delete a file from the database."""
    # GIVEN a housekeeper api with a file
    hk_file: File = populated_housekeeper_api.files().first()

    # GIVEN the id of a file that exists in HK
    assert hk_file

    # WHEN deleting the file
    populated_housekeeper_api.delete_file(hk_file.id)

    # THEN assert the file was removed
    assert populated_housekeeper_api.get_file(hk_file.id) is None


def test_get_included_path(populated_housekeeper_api: HousekeeperAPI, case_id: str):
    """Test to get the included path for a file."""
    # GIVEN a populated housekeeper api and the root dir
    root_dir: Path = Path(populated_housekeeper_api.get_root_dir())

    # GIVEN a version and a file object
    version: Version = populated_housekeeper_api.last_version(case_id)
    hk_file: File = version.files[0]

    # WHEN fetching the included path
    included_path: Path = populated_housekeeper_api.get_included_path(
        root_dir=root_dir, version_obj=version, file_obj=hk_file
    )

    # THEN assert that there is no file existing in the included path
    assert included_path.exists() is False

    # THEN assert that the correct path was created
    assert included_path == Path(root_dir, version.relative_root_dir, Path(hk_file.path).name)


def test_get_include_file(populated_housekeeper_api: HousekeeperAPI, case_id: str):
    """Test to get the included path for a file."""
    # GIVEN a populated housekeeper api and the root dir
    root_dir: Path = Path(populated_housekeeper_api.get_root_dir())
    version: Version = populated_housekeeper_api.last_version(case_id)
    hk_file: File = version.files[0]
    original_path: Path = Path(hk_file.path)
    included_path: Path = Path(root_dir, version.relative_root_dir, original_path.name)

    # GIVEN that the included file does not exist
    assert included_path.exists() is False

    # WHEN including the file
    included_file = populated_housekeeper_api.include_file(hk_file, version)

    # THEN assert that the file has been linked to the included place
    assert included_path.exists() is True

    # THEN assert that the file path has been updated
    assert included_file.path != original_path


def test_include_files_to_latest_version_when_included(
    caplog, case_id: str, populated_housekeeper_api: HousekeeperAPI
):
    """Test to include files for a bundle."""
    # GIVEN a populated Housekeeper API and the root dir
    root_dir: Path = Path(populated_housekeeper_api.get_root_dir())
    version: Version = populated_housekeeper_api.last_version(case_id)
    hk_file: File = version.files[0]
    original_path: Path = Path(hk_file.path)
    included_dir_path: Path = Path(root_dir, version.relative_root_dir)
    included_dir_path.mkdir(parents=True, exist_ok=True)
    included_path: Path = Path(included_dir_path, original_path.name)
    included_path.touch()

    # GIVEN that the included file does exist
    assert included_path.exists() is True

    # WHEN including the file
    populated_housekeeper_api.include_files_to_latest_version(bundle_name=case_id)

    hk_version: Version = populated_housekeeper_api.get_latest_bundle_version(bundle_name=case_id)
    included_file: File = hk_version.files[0]

    # THEN assert that the file is still linked to the included place
    assert included_path.exists() is True

    # THEN assert that the file path is unchanged
    assert included_file.path == original_path.as_posix()

    assert f"File is already included in Housekeeper for bundle: {case_id}" in caplog.text


def test_include_files_to_latest_version(
    case_id: str,
    madeline_output: Path,
    not_existing_hk_tag: str,
    populated_housekeeper_api: HousekeeperAPI,
):
    """Test to include files for a bundle."""
    # GIVEN a populated Housekeeper API and the root dir
    root_dir: Path = Path(populated_housekeeper_api.get_root_dir())
    version: Version = populated_housekeeper_api.last_version(case_id)
    hk_file: File = version.files[0]
    original_path: Path = Path(hk_file.path)
    included_path: Path = Path(root_dir, version.relative_root_dir, original_path.name)

    # GIVEN that the included file does not exist
    assert included_path.exists() is False

    new_file: File = populated_housekeeper_api.add_file(
        path=madeline_output, version_obj=version, tags=not_existing_hk_tag
    )
    populated_housekeeper_api.commit()

    assert Path(new_file.path).parent != included_path.parent

    # WHEN including the file
    populated_housekeeper_api.include_files_to_latest_version(bundle_name=case_id)

    hk_version: Version = populated_housekeeper_api.get_latest_bundle_version(bundle_name=case_id)

    # THEN all files in bundle should be included
    for file in hk_version.files:
        assert file.is_included

    # THEN assert that the file path has been updated
    included_madelaine_file: File = populated_housekeeper_api.get_file(file_id=new_file.id)
    assert Path(included_madelaine_file.full_path).parent == included_path.parent


def test_check_bundle_files(
    case_id: str,
    timestamp_yesterday: datetime,
    populated_housekeeper_api: HousekeeperAPI,
    hk_version: Version,
    fastq_file: Path,
    sample_id: str,
    bed_file: Path,
):
    """Test to see if the function correctly identifies a file that is present and returns a lis without it."""
    # GIVEN a housekeeper version with a file
    version: Version = populated_housekeeper_api.version(bundle=case_id, date=timestamp_yesterday)

    # WHEN attempting to add two files, one existing and one new
    files_to_add: list[Path] = populated_housekeeper_api.check_bundle_files(
        file_paths=[bed_file, fastq_file],
        bundle_name=case_id,
        last_version=version,
    )

    # Then only the new file should be returned
    assert files_to_add == [fastq_file]


def test_get_tag_names_from_file(populated_housekeeper_api: HousekeeperAPI):
    """Test get tag names on a file."""
    # GIVEN a housekeeper api with a file
    hk_file = populated_housekeeper_api.files().first()
    assert hk_file.tags

    # WHEN fetching tags of a file
    tag_names = populated_housekeeper_api.get_tag_names_from_file(hk_file)

    # THEN a list of tag names is returned
    assert tag_names is not None

    # THEN the return type is a list of strings
    assert isinstance(tag_names, list)
    assert all(isinstance(elem, str) for elem in tag_names)


def test_is_fastq_or_spring_in_all_bundles_when_none(
    populated_housekeeper_api: HousekeeperAPI,
    case_id: str,
    tags: list[str],
):
    """Test checking if all FASTQ or SPRING files are present in bundles when no files are present."""
    # GIVEN a populated housekeeper api with some files

    # WHEN fetching all files
    was_true = populated_housekeeper_api.is_fastq_or_spring_in_all_bundles(bundle_names=[case_id])

    # THEN assert all file were not present in all bundles
    assert not was_true


def test_is_fastq_or_spring_in_all_bundles(
    populated_housekeeper_api: HousekeeperAPI,
    case_id: str,
    madeline_output: Path,
    tags: list[str],
):
    """Test checking if all FASTQ or SPRING files are present in bundles when files are present."""
    # GIVEN a populated housekeeper api with some files

    # GIVEN a FASTQ file tag with a file included the bundle
    populated_housekeeper_api.add_and_include_file_to_latest_version(
        file=madeline_output, bundle_name=case_id, tags=[SequencingFileTag.FASTQ]
    )

    # WHEN fetching all files
    was_true = populated_housekeeper_api.is_fastq_or_spring_in_all_bundles(bundle_names=[case_id])

    # THEN assert all file were present in all bundles
    assert was_true


def test_is_fastq_or_spring_in_all_bundles_when_missing(
    populated_housekeeper_api: HousekeeperAPI,
    case_id: str,
    madeline_output: Path,
    new_bundle_name: str,
    tags: list[str],
):
    """Test checking if all FASTQ or SPRING files are present in bundles when not all bundles have files present."""
    # GIVEN a populated housekeeper api with some files
    version: Version = populated_housekeeper_api.last_version(case_id)

    # GIVEN a FASTQ file tag in the bundle
    populated_housekeeper_api.add_file(
        path=madeline_output, version_obj=version, tags=[SequencingFileTag.FASTQ]
    )

    # GIVEN an empty bundle
    populated_housekeeper_api.create_new_bundle_and_version(name=new_bundle_name)

    populated_housekeeper_api.commit()

    # WHEN fetching all files
    was_true = populated_housekeeper_api.is_fastq_or_spring_in_all_bundles(
        bundle_names=[case_id, new_bundle_name]
    )

    # THEN assert all file were not present in all bundles
    assert not was_true


def test_is_fastq_or_spring_in_all_bundles_when_multiple_bundles(
    case_id: str,
    compression_object: MockCompressionData,
    populated_housekeeper_api: HousekeeperAPI,
    madeline_output: Path,
    new_bundle_name: str,
    tags: list[str],
):
    """Test checking if all FASTQ or SPRING files are present in bundles when all bundles have files present."""
    # GIVEN a populated housekeeper api with some files

    # GIVEN a FASTQ file tag with a file included the bundle
    populated_housekeeper_api.add_and_include_file_to_latest_version(
        file=madeline_output, bundle_name=case_id, tags=[SequencingFileTag.FASTQ]
    )

    # GIVEN an empty bundle
    populated_housekeeper_api.create_new_bundle_and_version(name=new_bundle_name)

    # GIVEN an existing SPRING metadata file
    compression_object.spring_metadata_path.touch()

    # GIVEN a SPRING file tag with a file included the bundle
    populated_housekeeper_api.add_and_include_file_to_latest_version(
        file=compression_object.spring_metadata_path,
        bundle_name=new_bundle_name,
        tags=[SequencingFileTag.SPRING_METADATA],
    )

    # WHEN fetching all files
    was_true = populated_housekeeper_api.is_fastq_or_spring_in_all_bundles(
        bundle_names=[case_id, new_bundle_name]
    )

    # THEN assert all file were present in all bundles
    assert was_true


def test_is_fastq_or_spring_in_all_bundles_when_multiple_bundles_and_files(
    case_id: str,
    compression_object: MockCompressionData,
    populated_housekeeper_api: HousekeeperAPI,
    madeline_output: Path,
    new_bundle_name: str,
    tags: list[str],
):
    """
    Test checking if all FASTQ or SPRING files are present in bundles when all bundles have files present and some
    both FASTQ and SPRING.
    """
    # GIVEN a populated Housekeeper API with some files

    # GIVEN a FASTQ file tag with a file included in the bundle
    populated_housekeeper_api.add_and_include_file_to_latest_version(
        file=madeline_output, bundle_name=case_id, tags=[SequencingFileTag.FASTQ]
    )

    # GIVEN an empty bundle
    populated_housekeeper_api.create_new_bundle_and_version(name=new_bundle_name)

    # GIVEN an existing SPRING metadata file
    compression_object.spring_metadata_path.touch()

    # GIVEN a SPRING file tag with a file included in the bundle
    populated_housekeeper_api.add_and_include_file_to_latest_version(
        file=compression_object.spring_metadata_path,
        bundle_name=new_bundle_name,
        tags=[SequencingFileTag.SPRING_METADATA],
    )

    # WHEN fetching all files
    was_true = populated_housekeeper_api.is_fastq_or_spring_in_all_bundles(
        bundle_names=[case_id, new_bundle_name]
    )

    # THEN assert all file were present in all bundles
    assert was_true


def test_is_fastq_or_spring_on_disk_in_all_bundles_when_none(
    populated_housekeeper_api: HousekeeperAPI,
    case_id: str,
    tags: list[str],
):
    """Test checking if all FASTQ or SPRING files are on disk in bundles when no files are on disk."""
    # GIVEN a populated housekeeper api with some files

    # WHEN fetching all files
    was_true = populated_housekeeper_api.is_fastq_or_spring_on_disk_in_all_bundles(
        bundle_names=[case_id]
    )

    # THEN assert all file were not on disk in all bundles
    assert not was_true


def test_is_fastq_or_spring_on_disk_in_all_bundles(
    populated_housekeeper_api: HousekeeperAPI,
    case_id: str,
    madeline_output: Path,
    tags: list[str],
):
    """Test checking if all FASTQ or SPRING files are on disk in bundles when files are on disk."""
    # GIVEN a populated housekeeper api with some files

    # GIVEN a FASTQ file tag with a file on disk the bundle
    populated_housekeeper_api.add_and_include_file_to_latest_version(
        file=madeline_output, bundle_name=case_id, tags=[SequencingFileTag.FASTQ]
    )

    # WHEN fetching all files
    was_true = populated_housekeeper_api.is_fastq_or_spring_on_disk_in_all_bundles(
        bundle_names=[case_id]
    )

    # THEN assert all file were on disk in all bundles
    assert was_true


def test_is_fastq_or_spring_on_disk_in_all_bundles_when_missing_file(
    populated_housekeeper_api: HousekeeperAPI,
    case_id: str,
    sample_id: str,
    madeline_output: Path,
    new_bundle_name: str,
    tags: list[str],
):
    """Test checking if all FASTQ or SPRING files are on disk in bundles when not all bundles have files on disk."""
    # GIVEN a populated housekeeper api with some files
    version: Version = populated_housekeeper_api.last_version(case_id)

    # GIVEN a FASTQ file tag in the bundle
    populated_housekeeper_api.add_file(
        path=madeline_output, version_obj=version, tags=[SequencingFileTag.FASTQ]
    )

    # GIVEN an empty bundle
    populated_housekeeper_api.create_new_bundle_and_version(name=new_bundle_name)

    # GIVEN a FASTQ file tag in the bundle, but not on disk
    populated_housekeeper_api.add_file(
        path="does_not_exist_on_disk", version_obj=version, tags=[SequencingFileTag.FASTQ]
    )

    populated_housekeeper_api.commit()

    # WHEN fetching all files
    was_true = populated_housekeeper_api.is_fastq_or_spring_on_disk_in_all_bundles(
        bundle_names=[case_id, new_bundle_name]
    )

    # THEN assert all file were not on disk in all bundles
    assert not was_true


def testis_fastq_or_spring_on_disk_in_all_bundles_when_multiple_bundles(
    case_id: str,
    compression_object: MockCompressionData,
    populated_housekeeper_api: HousekeeperAPI,
    madeline_output: Path,
    new_bundle_name: str,
    tags: list[str],
):
    """Test checking if all FASTQ or SPRING files are on disk in bundles when all bundles have files on disk."""
    # GIVEN a populated housekeeper api with some files

    # GIVEN a FASTQ file tag with a file included the bundle
    populated_housekeeper_api.add_and_include_file_to_latest_version(
        file=madeline_output, bundle_name=case_id, tags=[SequencingFileTag.FASTQ]
    )

    # GIVEN an empty bundle
    populated_housekeeper_api.create_new_bundle_and_version(name=new_bundle_name)

    # GIVEN an existing SPRING metadata file
    compression_object.spring_metadata_path.touch()

    # GIVEN a SPRING file tag with a file included the bundle
    populated_housekeeper_api.add_and_include_file_to_latest_version(
        file=compression_object.spring_metadata_path,
        bundle_name=new_bundle_name,
        tags=[SequencingFileTag.SPRING_METADATA],
    )

    # WHEN fetching all files
    was_true = populated_housekeeper_api.is_fastq_or_spring_on_disk_in_all_bundles(
        bundle_names=[case_id, new_bundle_name]
    )

    # THEN assert all file were on disk in all bundles
    assert was_true


def test_get_non_archived_spring_path_and_bundle_name(populated_housekeeper_api: HousekeeperAPI):
    """Test fetching the path and associated bundle for each non-archived SPRING file."""
    # GIVEN a housekeeper_api containing spring_files which are not archived

    # WHEN fetching all non-archived spring baths and bundle names
    files_and_bundle_names: list[tuple[str, str]] = (
        populated_housekeeper_api.get_non_archived_spring_path_and_bundle_name()
    )
    assert len(files_and_bundle_names) > 0
    # THEN each file should be a spring file
    # THEN none of the files should have an archive
    # THEN each of the files should have a corresponding bundle name
    for bundle_name, file in files_and_bundle_names:
        housekeeper_file: File = populated_housekeeper_api.files(path=file).first()
        assert SequencingFileTag.SPRING in [tag.name for tag in housekeeper_file.tags]
        assert not housekeeper_file.archive
        assert bundle_name == housekeeper_file.version.bundle.name


def test_get_file_insensitive_path(bed_file: Path, populated_housekeeper_api: HousekeeperAPI):
    """Test that a file is fetched given its path."""
    # GIVEN the path of a file in Housekeeper API

    # WHEN getting the file though the path
    file: File = populated_housekeeper_api.get_file_insensitive_path(path=bed_file)

    # THEN the file is fetched correctly
    assert file


def test_get_files_containing_tags(
    populated_housekeeper_api: HousekeeperAPI, sample_id: str, fastq_file: Path, spring_file: Path
):
    """Test get files containing specific tags."""

    # GIVEN a populated Housekeeper API and a list of sample files
    files: list[File] = populated_housekeeper_api.get_files_from_latest_version(sample_id)
    files_names: list[str] = [Path(file.full_path).name for file in files]
    assert spring_file.name in files_names
    assert fastq_file.name in files_names

    # GIVEN a list of fastq file tags
    tags: list[set[str]] = [{SequencingFileTag.FASTQ}]

    # WHEN getting a list of files with tags
    filtered_files: list[File] = populated_housekeeper_api.get_files_containing_tags(
        files=files, tags=tags
    )

    # THEN only the expected fastq sample files should be retrieved
    filtered_files_names: list[str] = [Path(file.full_path).name for file in filtered_files]
    assert fastq_file.name in filtered_files_names
    assert spring_file.name not in filtered_files_names


def test_get_files_when_using_no_tags(
    populated_housekeeper_api: HousekeeperAPI, sample_id: str, empty_list: list
):
    """Test get files containing an empty list of tags."""

    # GIVEN a populated Housekeeper API and a list of sample files
    files: list[File] = populated_housekeeper_api.get_files_from_latest_version(sample_id)

    # WHEN getting a list of files providing an empty list of tags
    filtered_files: list[File] = populated_housekeeper_api.get_files_containing_tags(
        files=files, tags=empty_list
    )

    # THEN an empty list should be returned
    assert filtered_files == empty_list


def test_filter_files_without_tags(
    populated_housekeeper_api: HousekeeperAPI, sample_id: str, fastq_file: Path, spring_file: Path
):
    """Test get files without specific tags."""

    # GIVEN a populated Housekeeper API and a list of sample files
    files: list[File] = populated_housekeeper_api.get_files_from_latest_version(sample_id)
    files_names: list[str] = [Path(file.full_path).name for file in files]
    assert spring_file.name in files_names
    assert fastq_file.name in files_names

    # GIVEN a list of fastq file tags to exclude
    excluded_tags: list[str] = [SequencingFileTag.FASTQ]

    # WHEN getting a list of files lacking excluded tags
    filtered_files: list[File] = populated_housekeeper_api.get_files_without_excluded_tags(
        files=files, excluded_tags=excluded_tags
    )

    # THEN only the expected sample spring files should be retrieved
    filtered_files_names: list[str] = [Path(file.full_path).name for file in filtered_files]
    assert spring_file.name in filtered_files_names
    assert fastq_file.name not in filtered_files_names


def test_get_files_without_excluded_tags_using_no_tags(
    populated_housekeeper_api: HousekeeperAPI,
    sample_id: str,
    fastq_file: Path,
    spring_file: Path,
    empty_list: list,
):
    """Test get files without tags for an empty tag input."""

    # GIVEN a populated Housekeeper API and a list of sample files
    files: list[File] = populated_housekeeper_api.get_files_from_latest_version(sample_id)

    # WHEN getting a list of files without tags when providing an empty list of tags
    filtered_files: list[File] = populated_housekeeper_api.get_files_without_excluded_tags(
        files=files, excluded_tags=empty_list
    )

    # THEN the complete list of original files should be returned
    assert filtered_files == files


def test_get_files_from_latest_version_containing_tags(
    populated_housekeeper_api: HousekeeperAPI, sample_id: str, fastq_file: Path, spring_file: Path
):
    """Test get files from latest version by tags."""

    # GIVEN a populated Housekeeper API

    # GIVEN a list of fastq file tags
    tags: list[set[str]] = [{SequencingFileTag.FASTQ}]

    # WHEN getting a list of files that match specific tags
    filtered_files: list[File] = (
        populated_housekeeper_api.get_files_from_latest_version_containing_tags(
            bundle_name=sample_id, tags=tags
        )
    )

    # THEN only the expected fastq sample files should be returned
    filtered_files_names: list[str] = [Path(file.full_path).name for file in filtered_files]
    assert fastq_file.name in filtered_files_names
    assert spring_file.name not in filtered_files_names


def test_get_files_from_latest_version_using_no_tags(
    populated_housekeeper_api: HousekeeperAPI,
    sample_id: str,
    fastq_file: Path,
    spring_file: Path,
    empty_list: list,
):
    """Test get files from the latest version by empty list of tags."""

    # GIVEN a populated Housekeeper API

    # WHEN getting a list of files that match empty tags
    filtered_files: list[File] = (
        populated_housekeeper_api.get_files_from_latest_version_containing_tags(
            bundle_name=sample_id, tags=empty_list
        )
    )

    # THEN an empty list should be returned
    assert filtered_files == empty_list


def test_get_files_from_latest_version_containing_tags_and_excluded_tags(
    populated_housekeeper_api: HousekeeperAPI, sample_id: str, fastq_file: Path, spring_file: Path
):
    """Test get files from the latest version by tags and excluded tags."""

    # GIVEN a populated Housekeeper API

    # GIVEN a list of sample id tags
    tags: list[set[str]] = [{sample_id}]

    # GIVEN a list of fastq file tags to exclude
    excluded_tags: list[str] = [SequencingFileTag.FASTQ]

    # WHEN getting a list of files that match the sample ID tag and exclude the fastq files
    filtered_files: list[File] = (
        populated_housekeeper_api.get_files_from_latest_version_containing_tags(
            bundle_name=sample_id, tags=tags, excluded_tags=excluded_tags
        )
    )

    # THEN only the expected fastq sample files should be returned
    filtered_files_names: list[str] = [Path(file.full_path).name for file in filtered_files]
    assert spring_file.name in filtered_files_names
    assert fastq_file.name not in filtered_files_names

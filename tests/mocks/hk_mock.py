"""Module for mocking out the HK api in CG"""

import datetime
import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Set

from housekeeper.store.models import Bundle, File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.exc import HousekeeperBundleVersionMissingError

ROOT_PATH = tempfile.TemporaryDirectory().name

LOG = logging.getLogger(__name__)


def calculate_checksum(path):
    """Calculate the checksum for a file"""
    _ = path
    return "asdjkfghasdkfj"


class MockTag:
    """Mocks a hk tag object"""

    def __init__(self, **kwargs):
        """Init a tag mock. Defaults name to 'vcf'"""
        self.id = kwargs.get("id", 1)
        self.name = kwargs.get("name", "vcf")
        self.category = kwargs.get("category")
        self.created_at = kwargs.get("created_at", datetime.datetime.now())

    def __repr__(self):
        return (
            f"MockTag:id={self.id}, name={self.name}, category={self.category},"
            f"created_at={self.created_at}"
        )


class MockFile:
    """Mocks a hk file object"""

    def __init__(self, **kwargs):
        """Init a file mock"""
        self.id = kwargs.get("id", 1)
        self.path = kwargs.get("path", "a_file")
        self.checksum = calculate_checksum(self.path)
        self.to_archive = kwargs.get("is_archiving_request", False)

        self.version_id = kwargs.get("version_id", 1)
        self.tags = kwargs.get("tags", [MockTag()])

        self.app_root = Path(kwargs.get("root_path", ROOT_PATH))

    @property
    def full_path(self):
        """Return the full path to the file."""
        return str(self.path)

    @property
    def is_included(self):
        """Check if the file is included in Housekeeper."""
        return str(self.app_root) in self.full_path

    @property
    def archive(self):
        return False

    def delete(self):
        """Mock delete functions"""
        return True

    def __repr__(self):
        return f"MockFile:id={self.id}, path={self.path}, is_archiving_request={self.to_archive}"


class MockVersion:
    """Mocks a hk version object"""

    def __init__(self, **kwargs):
        """Init a version mock"""
        self.id = kwargs.get("id", 1)
        self.created_at = kwargs.get("created_at", datetime.datetime.now())
        self.expires_at = kwargs.get("expires_at")
        self.included_at = kwargs.get("included_at")
        self.removed_at = kwargs.get("removed_at")

        self.archived_at = kwargs.get("archived_at")
        self.archive_path = kwargs.get("archive_path")
        self.archive_checksum = kwargs.get("archive_checksum")

        self.bundle = kwargs.get("bundle")
        self.bundle_name = kwargs.get("bundle", "bundle_name")
        self.bundle_id = kwargs.get("bundle_id", 1)

        self.files = kwargs.get("files", [])

        self.app_root = kwargs.get("root_path", ROOT_PATH)

    @property
    def relative_root_dir(self):
        """Build the relative root dir path for the bundle version."""
        return Path(self.bundle_name) / str(self.created_at.date())

    @property
    def full_path(self):
        """Returns the full path of the bundle"""
        return Path(self.app_root) / self.bundle.name / str(self.created_at.date())

    def __repr__(self):
        return f"MockVersion:id={self.id}, created_at={self.created_at}, files={self.files}"


class QueryList(list):
    """Create a list that mocks the behaviour of a query result"""

    def __init__(self):
        super(QueryList, self).__init__()

    def first(self):
        """Mock the first method"""
        if len(self) == 0:
            return None
        return self[0]

    def count(self):
        """Mock the count method"""
        return len(self)

    def all(self):
        """Mock the all method"""
        return self


class MockBundle:
    """Mocks a hk bundle object"""

    def __init__(self, **kwargs):
        """Init a bundle mock"""
        self.id = kwargs.get("id", 1)
        self.name = kwargs.get("name", "yellowhog")
        self.created_at = kwargs.get("created_at", datetime.datetime.now())
        self.versions = kwargs.get("versions", [])

    def __repr__(self):
        return f"MockBundle:id={self.id}, name={self.name}, versions={self.versions}"


class MockHousekeeperAPI:
    """Mocks all the behaviour of the housekeeper API"""

    def __init__(self, config=None):
        self._version_obj = None
        self._bundle_obj = None
        self._files = QueryList()
        self._tags = QueryList()
        self._bundles = QueryList()
        self._id_counter = 1
        self._file_added = False
        self._file_included = False
        self._tags_matter = False
        self._last_version = True
        # Add tags here if there should be missing files
        self._missing_tags = set()
        if not config:
            config = {
                "housekeeper": {
                    "database": "sqlite:///:memory:",
                    "root": str(ROOT_PATH),
                }
            }
        self._database = config.get("housekeeper", {}).get("database")
        self.root_path = config.get("housekeeper", {}).get("root", str(ROOT_PATH))

    # Mock specific functions
    def get_file_from_version(self, version: Version, tags: Set[str]):
        if tags.intersection(self._missing_tags):
            return None
        return self._files[0]

    def get_latest_file_from_version(self, version: Version, tags: Set[str]):
        if tags.intersection(self._missing_tags):
            return None
        return self._files[-1]

    def get_latest_file(
        self, bundle: str, tags: list | None = None, version: int | None = None
    ) -> File | None:
        if tags.intersection(self._missing_tags):
            return None
        return self._files[0]

    def get_file_from_latest_version(self, bundle_name: str, tags: list[str]) -> File | None:
        """Find a file in the latest version of a bundle."""
        version: Version = self.last_version(bundle=bundle_name)
        if not version:
            LOG.info(f"Bundle: {bundle_name} not found in Housekeeper")
            raise HousekeeperBundleVersionMissingError
        return self.files(version=version.id, tags=tags).first()

    def get_files_from_latest_version_containing_tags(self, **_kwargs) -> list[File]:
        return self._files.all()

    def get_files_from_latest_version(
        self, bundle_name: str, tags: list[str] | None = None
    ) -> list[File] | None:
        """Return files in the latest version of a bundle."""
        version: Version = self.last_version(bundle=bundle_name)
        if not version:
            LOG.info(f"Bundle: {bundle_name} not found in Housekeeper")
            raise HousekeeperBundleVersionMissingError
        return self.files(version=version.id, tags=tags)

    def add_missing_tag(self, tag_name: str):
        """Add a missing tag"""
        self._missing_tags.add(tag_name)

    def set_missing_last_version(self):
        """Make sure that no version is returned"""
        self._last_version = False

    def is_file_included(self) -> bool:
        """Return true if any file has been included"""
        return self._file_included

    def is_file_added(self) -> bool:
        """Return true if any file has been added"""
        return self._file_added

    def tag_exists(self, tag_name) -> bool:
        """Return true if a tag has been added"""
        for tag_obj in self._tags:
            if tag_obj.name == tag_name:
                return True
        return False

    def file_exists(self, file_path) -> bool:
        """Return true if a file has been added"""
        file_name = Path(file_path).name
        for file_obj in self._files:
            if Path(file_obj.path).name == file_name:
                return True
        return False

    def update_id_counter(self):
        """Increment id counter"""
        self._id_counter += 1

    # Mocked functions from original API
    def add_bundle(self, bundle_data):
        """Build a new bundle version of files"""
        bundle_obj = self.new_bundle(name=bundle_data["name"], created_at=bundle_data["created"])

        version_obj = self.new_version(
            created_at=bundle_data["created"], expires_at=bundle_data.get("expires")
        )

        tag_names = set(
            tag_name for file_data in bundle_data["files"] for tag_name in file_data["tags"]
        )
        tag_map = self._build_tags(tag_names)
        for file_data in bundle_data["files"]:
            if isinstance(file_data["path"], str):
                paths = [file_data["path"]]
            else:
                paths = file_data["path"]
            for path in paths:
                tags = [tag_map[tag_name] for tag_name in file_data["tags"]]

                new_file = self.new_file(path, to_archive=file_data["archive"], tags=tags)
                self._files.append(new_file)
                self._file_added = True
                version_obj.files.append(new_file)
        version_obj.bundle_obj = bundle_obj
        bundle_obj.versions.append(version_obj)
        return bundle_obj, version_obj

    def _build_tags(self, tag_names: list[str]) -> dict:
        """Build a list of tag objects."""
        tags = {}
        for tag_name in tag_names:
            if self.tag_exists(tag_name):
                tag_obj = self.get_tag(tag_name)
            else:
                tag_obj = self.new_tag(tag_name)
                self._tags.append(tag_obj)
            tags[tag_name] = tag_obj
        return tags

    def get_tag(self, name: str):
        """Fetch a tag"""
        for tag_obj in self._tags:
            if tag_obj.name == name:
                return tag_obj
        return None

    def bundle(self, name: str) -> MockBundle:
        """Fetch a bundle"""
        if name:
            for bundle_obj in self.bundles():
                if bundle_obj.name == name:
                    return bundle_obj
        return self._bundle_obj

    def bundles(self):
        """Fetch bundles"""
        return self._bundles

    def new_bundle(self, name: str, created_at: datetime.datetime = None):
        """Create a new file bundle"""
        self.update_id_counter()
        bundle_obj = MockBundle(id=self._id_counter, name=name, created_at=created_at)
        self._bundle_obj = bundle_obj
        self._bundles.append(bundle_obj)
        return bundle_obj

    def get_version_by_id(self, *args, **kwargs):
        """Fetch a version by id"""
        return self._version_obj

    def get_or_create_version(self, bundle_name: str):
        """Returns the latest version of a bundle if it exists. If no creates a bundle and returns its version"""
        last_version = self.last_version(bundle=bundle_name)
        if not last_version:
            LOG.info(f"Creating bundle for sample {bundle_name} in housekeeper")
            bundle_result = self.add_bundle(
                bundle_data={
                    "name": bundle_name,
                    "created": datetime.datetime.now(),
                    "expires": None,
                    "files": [],
                }
            )
            last_version = bundle_result[1]
        return last_version

    def files(self, *args, **kwargs):
        """
        Fetch files.
        If it has been specified that some files should be missing return empty list
        """
        tags = set(kwargs.get("tags", []))
        if tags.intersection(self._missing_tags):
            return QueryList()
        return self._files

    def new_tag(self, name: str, category: str = None):
        """Create a new tag"""
        self.update_id_counter()
        tag_obj = MockTag(id=self._id_counter, name=name, category=category)
        if not self.tag_exists(name):
            self._tags.append(tag_obj)

        return tag_obj

    def add_tag(self, name: str, category: str = None):
        """Add a tag to the database"""
        tag_obj = self.new_tag(name, category)
        if not self.tag_exists(name):
            self._tags.append(tag_obj)
        return tag_obj

    def new_version(self, created_at: datetime.datetime, expires_at: datetime.datetime = None):
        """Create a new bundle version"""
        self.update_id_counter()
        created_at = created_at or datetime.datetime.now()
        expires_at = expires_at or datetime.datetime.now()
        version_obj = MockVersion(id=self._id_counter, created_at=created_at, expires_at=expires_at)
        self._version_obj = version_obj
        return version_obj

    def add_version(
        self,
        version_obj: MockVersion = None,
        created_at: datetime.datetime = None,
        expires_at: datetime.datetime = None,
    ):
        """Create a new bundle version"""
        if not version_obj:
            version_obj = self.new_version(created_at, expires_at)
        self._version_obj = version_obj
        return version_obj

    def new_file(
        self,
        path: str,
        checksum: str = None,
        to_archive: bool = False,
        tags: list = [],
    ):
        """Create a new file"""
        self.update_id_counter()
        mocked_file = MockFile(
            id=self._id_counter,
            path=path,
            checksum=checksum,
            to_archive=to_archive,
            tags=tags,
        )
        if not self.file_exists(path):
            self._files.append(mocked_file)
        self._file_added = True
        return mocked_file

    def add_commit(self, *args, **kwargs):
        """Wrap method in Housekeeper Store"""
        return True

    def commit(self):
        """Wrap method in Housekeeper Store"""
        return True

    def include(self, *args, **kwargs):
        """Call the include version function to import related assets."""
        self._file_included = True

    def include_file(self, *args, **kwargs):
        """Call the include version function to import related assets."""
        self._file_included = True

    def last_version(self, *args, **kwargs):
        """Gets the latest version of a bundle."""
        if self._last_version is False:
            return None
        if len(args) > 0:
            bundle = self.bundle(args[0])
            if bundle:
                return bundle.versions[-1]
        return self._version_obj

    def get_latest_bundle_version(self, bundle_name: str):
        """Get latest version of a bundle or log."""
        last_version = self.last_version(bundle_name)
        if not last_version:
            LOG.warning(f"No bundle found for {bundle_name} in Housekeeper")
            return None
        LOG.debug(f"Found version obj for {bundle_name}: {repr(last_version)}")
        return last_version

    def get_root_dir(self):
        """Returns the root dir of Housekeeper."""

        return self.root_path

    def get_files(self, *args, **kwargs):
        """Fetch all the files in housekeeper, optionally filtered by bundle and/or tags and/or
        version

        Returns:
            iterable(hk.Models.File)
        """
        return self.files(*args, **kwargs)

    def get_file_insensitive_path(self, path: Path) -> File | None:
        """Returns a file in Housekeeper with a path that matches the given path, insensitive to whether the paths
        are included or not."""
        file: File = self.files(path=path.as_posix()).first()
        if not file:
            if path.is_absolute():
                file = self.files(path=str(path).replace(self.root_path, "")).first()
            else:
                file = self.files(path=self.root_path + str(path)).first()
        return file

    def add_file(self, path, version_obj, tags, to_archive=False):
        """Add a file to housekeeper."""
        tags = tags or []
        if isinstance(tags, str):
            tags = [tags]
        for tag_name in tags:
            if not self.get_tag(tag_name):
                self.add_tag(tag_name)

        new_file = self.new_file(
            path=str(Path(path).absolute()),
            to_archive=to_archive,
            tags=[self.get_tag(tag_name) for tag_name in tags],
        )
        if not version_obj:
            version_obj = self.new_version(created_at=datetime.datetime.now())
        new_file.version = version_obj
        if not self.file_exists(path):
            self._files.append(new_file)
        self._file_added = True
        version_obj.files.append(new_file)
        return new_file

    def check_bundle_files(
        self, bundle_name: str, file_paths: list[Path], last_version, tags: list | None = None
    ) -> list[Path]:
        """Checks if any of the files in the provided list are already added to the provided bundle. Returns a list of files that have not been added"""
        for file in self.get_files(bundle=bundle_name, tags=tags, version=last_version.id):
            if Path(file.path) in file_paths:
                file_paths.remove(Path(file.path))
                LOG.info(
                    "Path %s is already linked to bundle %s in housekeeper"
                    % (file.path, bundle_name)
                )
        return file_paths

    def create_new_bundle_and_version(self, name: str) -> Bundle:
        """Create new bundle with version"""
        new_bundle = self.new_bundle(name=name)
        self.add_commit(new_bundle)
        new_version = self.new_version(created_at=new_bundle.created_at)
        new_bundle.versions.append(new_version)
        self.commit()
        LOG.info("New bundle created with name %s", new_bundle.name)
        return new_bundle

    def add_and_include_file_to_latest_version(
        self, bundle_name: str, file: Path, tags: list
    ) -> None:
        """Adds and includes a file in the latest version of a bundle."""
        version: Version = self.get_or_create_version(bundle_name)
        if not version:
            LOG.info(f"Bundle: {bundle_name} not found in housekeeper")
            raise HousekeeperBundleVersionMissingError
        hk_file: File = self.add_file(version_obj=version, tags=tags, path=str(file.absolute()))
        self.include_file(version_obj=version, file_obj=hk_file)
        self.commit()

    def include_files_to_latest_version(self, bundle_name: str) -> None:
        """Include all files in the latest version on a bundle."""
        bundle_version: Version = self.get_latest_bundle_version(bundle_name=bundle_name)
        self.include(version_obj=bundle_version)
        self.commit()

    def is_fastq_or_spring_in_all_bundles(self, bundle_names: list[str]) -> bool:
        """Return whether or not all FASTQ/SPRING files are included for the given bundles."""
        sequencing_files_in_hk: dict[str, bool] = {}
        for bundle_name in bundle_names:
            sequencing_files_in_hk[bundle_name] = False
            for tag in [SequencingFileTag.FASTQ, SequencingFileTag.SPRING_METADATA]:
                sample_file_in_hk: list[bool] = []
                hk_files: list[File] | None = self.get_files_from_latest_version(
                    bundle_name=bundle_name, tags=[tag]
                )
                sample_file_in_hk += [True for hk_file in hk_files if hk_file.is_included]
                if sample_file_in_hk:
                    break
            sequencing_files_in_hk[bundle_name] = (
                all(sample_file_in_hk) if sample_file_in_hk else False
            )
        return all(sequencing_files_in_hk.values())

    def delete_file(self, file_id: int) -> File | None:
        """Mock deleting a file both from database and disk (if included)."""
        file_obj = self._get_mock_file(file_id)
        if not file_obj:
            LOG.info(f"Could not find file {file_id}")
            return

        if file_obj.is_included and Path(file_obj.full_path).exists():
            LOG.info(f"Deleting file {file_obj.full_path} from disc")
            Path(file_obj.full_path).unlink()

        LOG.info(f"Deleting file {file_id} from mock housekeeper")
        self._files.remove(file_obj)

        return file_obj

    def _get_mock_file(self, file_id: int) -> File | None:
        for file_obj in self._files:
            if file_obj.id == file_id:
                return file_obj
        return None

    def get_non_archived_files_for_bundle(
        self, bundle_name: str, tags: list | None = None
    ) -> list[File]:
        """Returns all non-archived files from a given bundle, tagged with the given tags."""
        pass

    def get_archived_files_for_bundle(
        self, bundle_name: str, tags: list | None = None
    ) -> list[File]:
        """Returns all archived files from a given bundle, tagged with the given tags."""
        pass

    @staticmethod
    def get_tag_names_from_file(file) -> [str]:
        """Fetch a tag"""
        return HousekeeperAPI.get_tag_names_from_file(file=file)

    @staticmethod
    def checksum(path):
        """Calculate the checksum"""
        return calculate_checksum(path)

    def initialise_db(self):
        """Create all tables in the store."""

    def destroy_db(self):
        """Drop all tables in the store"""

    @contextmanager
    def session_no_autoflush(self):
        """Wrap property in Housekeeper Store"""
        yield True

    def rollback(self) -> None:
        return None

    def __repr__(self):
        return f"HousekeeperMockAPI:version_obj={self._version_obj}"


if __name__ == "__main__":
    hk_api = MockHousekeeperAPI(config={})

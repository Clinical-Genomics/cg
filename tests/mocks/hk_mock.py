"""Module for mocking out the HK api in CG"""

import datetime
import logging
import tempfile
from pathlib import Path
from typing import List

ROOT_PATH = tempfile.TemporaryDirectory()

LOG = logging.getLogger(__name__)


def calculate_checksum(path):
    """Calculate the checksum for a file"""
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
            f"MockTag:id={self.id},name={self.name},category={self.category},"
            f"created_at={self.created_at}"
        )


class MockFile:
    """Mocks a hk file object"""

    def __init__(self, **kwargs):
        """Init a file mock"""
        self.id = kwargs.get("id", 1)
        self.path = kwargs.get("path", "a_file")
        self.checksum = calculate_checksum(self.path)
        self.to_archive = kwargs.get("to_archive", False)

        self.version_id = kwargs.get("version_id", 1)
        self.tags = kwargs.get("tags", [MockTag()])

        self.app_root = kwargs.get("root_path", ROOT_PATH)

        @property
        def full_path(self):
            """Return the full path to the file."""
            if Path(self.path).is_absolute():
                return self.path
            return str(self.app_root / self.path)

        @property
        def is_included(self):
            """Check if the file is included in Housekeeper."""
            return str(self.app_root) in self.full_path


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

        self.files = kwargs.get("files", [MockFile()])

        self.app_root = kwargs.get("root_path", ROOT_PATH)

    @property
    def relative_root_dir(self):
        """Build the relative root dir path for the bundle version."""
        return Path(self.bundle_name) / str(self.created_at.date())

    @property
    def full_path(self):
        """Returns the full path of the bundle"""
        return Path(self.app_root) / self.bundle.name / str(self.created_at.date())


class MockBundle:
    """Mocks a hk bundle object"""

    def __init__(self, **kwargs):
        """Init a bundle mock"""
        self.id = kwargs.get("id", 1)
        self.name = kwargs.get("name", "yellowhog")
        self.created_at = kwargs.get("created_at", datetime.datetime.now())
        self.versions = kwargs.get("versions", [MockVersion(bundle=self)])


class MockHK:
    """Mocks all the behaviour of the housekeeper API"""

    def __init__(self, config):
        """Initialize a mock"""
        self.root_dir = config.get("housekeeper", {}).get("root",)
        # MOCK SPECIFIC HELPERS
        self._file_added = False
        self._file_included = False
        self._file = None
        self._files = []

        self._version = None
        self._versions = []

        self._tag = None
        self._tags = []

        self._bundle = None
        self._bundles = []

        self._store = {
            "files": self._files,
            "tags": self._tags,
            "bundles": self._bundles,
            "versions": self._versions,
        }

    def files(
        self,
        *,
        bundle: str = None,
        tags: List[str] = None,
        version: int = None,
        path: str = None,
    ):
        """ Fetch files """
        return self._files

    def new_file(
        self,
        path: str,
        checksum: str = None,
        to_archive: bool = False,
        tags: list = None,
    ):
        """ Create a new file """
        file_obj = MockFile(path=path, to_archive=to_archive, tags=tags)
        self._files.append(file_obj)
        return file_obj

    def tag(self, name: str):
        """ Fetch a tag """
        tag_found = self._tag
        for tag in self._store["tags"]:
            if tag.name == name:
                tag_found = tag
        return tag_found

    def new_tag(self, name: str, category: str = None):
        """ Create a new tag """
        tag_obj = MockTag(name=name, category=category)
        self._tag = tag_obj
        self._tags.append(tag_obj)
        return tag_obj

    def bundle(self, name: str):
        """ Fetch a bundle """
        bundle_found = self._bundle
        for bundle in self._store["bundles"]:
            if bundle.name == name:
                bundle_found = bundle
        return bundle_found

    def add_bundle(self, bundle_data: dict):
        """ Build a new bundle version of files """
        return self._bundles.append(MockBundle(**bundle_data))

    def bundles(self):
        """ Fetch bundles """
        return self._bundles

    @staticmethod
    def new_bundle(name: str, created_at: datetime.datetime = None):
        """ Create a new file bundle """
        return MockBundle(name=name, created_at=created_at)

    def version(self, bundle: str, date: datetime.datetime):
        """ Fetch a version """
        return self._version

    def last_version(self, bundle: str) -> MockVersion:
        """Gets the latest version of a bundle"""
        return self._version

    @staticmethod
    def new_version(
        created_at: datetime.datetime, expires_at: datetime.datetime = None
    ):
        """ Create a new bundle version """
        version_obj = MockVersion(created_at=created_at, expires_at=expires_at)
        self._version = version_obj
        self._versions.append(version_obj)
        return version_obj

    @staticmethod
    def add_commit(*args, **kwargs):
        """ Wrap method in Housekeeper Store """
        return True

    @staticmethod
    def commit():
        """ Wrap method in Housekeeper Store """
        return True

    @staticmethod
    def session_no_autoflush():
        """ Wrap property in Housekeeper Store """
        return True

    @staticmethod
    def include(version_obj: MockVersion):
        """Call the include version function to import related assets."""
        version_obj.included_at = datetime.datetime.now()

    @staticmethod
    def include_file(file_obj: MockFile, version_obj: MockVersion):
        """Call the include version function to import related assets."""
        return True

    def get_root_dir(self):
        """Returns the root dir of Housekeeper"""
        return self.root_dir

    def get_files(self, bundle: str, tags: list, version: int = None):
        """Fetch all the files in housekeeper, optionally filtered by bundle and/or tags and/or
        version

        Returns:
            iterable(MockFile)
        """
        return self._files

    def add_file(self, file, version_obj: MockVersion, tags, to_archive=False):
        """Add a file to housekeeper."""
        self._file_added = True
        file_obj = MockFile(path=file)
        self._file = file_obj
        self._files.append(file_obj)

        return file_obj

    @staticmethod
    def checksum(path):
        """Calculate the checksum"""
        return calculate_checksum(path)

    @staticmethod
    def initialise_db():
        """Create all tables in the store."""
        return True

    def destroy_db(self):
        """Drop all tables in the store"""
        self._store = {}


if __name__ == "__main__":
    hk_api = MockHK(config={})
    print(hk_api)

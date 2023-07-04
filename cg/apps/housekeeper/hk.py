""" Module to decouple cg code from Housekeeper code """
import datetime as dt
import logging
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from cg.constants import SequencingFileTag
from cg.exc import HousekeeperBundleVersionMissingError
from sqlalchemy.orm import Query

from housekeeper.include import checksum as hk_checksum
from housekeeper.include import include_version
from housekeeper.store import Store, models
from housekeeper.store.models import Bundle, File, Version

LOG = logging.getLogger(__name__)


class HousekeeperAPI:
    """API to decouple cg code from Housekeeper"""

    def __init__(self, config: dict) -> None:
        self._store = Store(config["housekeeper"]["database"], config["housekeeper"]["root"])
        self.root_dir: str = config["housekeeper"]["root"]

    def __getattr__(self, name):
        LOG.warning("Called undefined %s on %s, please wrap", name, self.__class__.__name__)
        return getattr(self._store, name)

    def new_bundle(self, name: str, created_at: dt.datetime = None) -> Bundle:
        """Create a new file bundle."""
        return self._store.new_bundle(name, created_at)

    def add_bundle(self, bundle_data) -> Tuple[Bundle, Version]:
        """Build a new bundle version of files."""
        return self._store.add_bundle(bundle_data)

    def bundle(self, name: str) -> Bundle:
        """Fetch a bundle."""
        return self._store.get_bundle_by_name(bundle_name=name)

    def bundles(self) -> List[Bundle]:
        """Fetch bundles."""
        return self._store.bundles()

    def create_new_bundle_and_version(self, name: str) -> Bundle:
        """Create new bundle with version."""
        new_bundle: Bundle = self.new_bundle(name=name)
        self.add_commit(new_bundle)
        new_version: Version = self.new_version(created_at=new_bundle.created_at)
        new_bundle.versions.append(new_version)
        self.commit()
        LOG.info(f"New bundle created with name {new_bundle.name}")
        return new_bundle

    def set_to_archive(self, file: File, value: bool) -> None:
        """Sets the 'to_archive' field of a file."""
        file.to_archive: bool = value
        self.commit()

    def new_file(
        self, path: str, checksum: str = None, to_archive: bool = False, tags: list = None
    ) -> File:
        """Create a new file."""
        if tags is None:
            tags = []
        return self._store.new_file(path, checksum, to_archive, tags)

    def get_file(self, file_id: int) -> Optional[File]:
        """Get a file based on file id."""
        LOG.info("Fetching file %s", file_id)
        file_obj: File = self._store.get_file_by_id(file_id=file_id)
        if not file_obj:
            LOG.info("file not found")
            return None
        return file_obj

    def delete_file(self, file_id: int) -> Optional[File]:
        """Delete a file both from database and disk (if included)."""
        file_obj: File = self.get_file(file_id)
        if not file_obj:
            LOG.info(f"Could not find file {file_id}")
            return

        if file_obj.is_included and Path(file_obj.full_path).exists():
            LOG.info(f"Deleting file {file_obj.full_path} from disc")
            Path(file_obj.full_path).unlink()

        LOG.info(f"Deleting file {file_id} from housekeeper")
        self._store.session.delete(file_obj)
        self.commit()

        return file_obj

    def add_file(self, path, version_obj: Version, tags: list, to_archive: bool = False) -> File:
        """Add a file to the database."""
        if isinstance(tags, str):
            tags: List[str] = [tags]
        for tag_name in tags:
            if not self.get_tag(tag_name):
                self.add_tag(tag_name)

        new_file: File = self.new_file(
            path=str(Path(path).absolute()),
            to_archive=to_archive,
            tags=[self.get_tag(tag_name) for tag_name in tags],
        )

        new_file.version: Version = version_obj
        return new_file

    def files(
        self,
        *,
        bundle: str = None,
        tags: Set[str] = None,
        version: int = None,
        path: str = None,
    ) -> Query:
        """Fetch files."""
        return self._store.get_files(
            bundle_name=bundle, tag_names=tags, version_id=version, file_path=path
        )

    @staticmethod
    def get_files_from_version(version: Version, tags: Set[str]) -> Optional[List[File]]:
        """Return a list of files associated with the given version and tags."""
        LOG.debug(f"Getting files from version with tags {tags}")
        files: List[File] = []
        for file in list(version.files):
            file_tags = {tag.name for tag in file.tags}
            if tags.issubset(file_tags):
                LOG.debug(f"Found file {file}")
                files.append(file)
        if not files:
            LOG.warning(f"Could not find any files matching the tags {tags}")
        return files

    @staticmethod
    def get_file_from_version(version: Version, tags: Set[str]) -> Optional[File]:
        """Return the first file matching the given tags."""
        files: List[File] = HousekeeperAPI.get_files_from_version(version=version, tags=tags)
        return files[0] if files else None

    @staticmethod
    def get_latest_file_from_version(version: Version, tags: Set[str]) -> Optional[File]:
        """Return the latest file from Housekeeper given its version and tags."""
        files: List[File] = HousekeeperAPI.get_files_from_version(version=version, tags=tags)
        return sorted(files, key=lambda file_obj: file_obj.id)[-1] if files else None

    def rollback(self):
        """Wrap method in Housekeeper Store."""
        return self._store.session.rollback()

    def session_no_autoflush(self):
        """Wrap property in Housekeeper Store."""
        return self._store.session.no_autoflush

    def get_files(
        self, bundle: str, tags: Optional[list] = None, version: Optional[int] = None
    ) -> Iterable[File]:
        """Get all the files in housekeeper, optionally filtered by bundle and/or tags and/or
        version.
        """
        return self._store.get_files(bundle_name=bundle, tag_names=tags, version_id=version)

    def get_latest_file(
        self, bundle: str, tags: Optional[list] = None, version: Optional[int] = None
    ) -> Optional[File]:
        """Return latest file from Housekeeper, filtered by bundle and/or tags and/or version."""
        files: Query = self._store.get_files(bundle_name=bundle, tag_names=tags, version_id=version)
        return files.order_by(File.id.desc()).first()

    def check_bundle_files(
        self,
        bundle_name: str,
        file_paths: List[Path],
        last_version: Version,
        tags: Optional[list] = None,
    ) -> List[Path]:
        """Checks if any of the files in the provided list are already added to the provided
        bundle. Returns a list of files that have not been added."""
        for file in self.get_files(bundle=bundle_name, tags=tags, version=last_version.id):
            if Path(file.path) in file_paths:
                file_paths.remove(Path(file.path))
                LOG.info(
                    f"Path {file.path} is already linked to bundle {bundle_name} in housekeeper"
                )
        return file_paths

    @staticmethod
    def get_included_path(root_dir: Path, version_obj: Version, file_obj: File) -> Path:
        """Generate the path to a file that should be included.
        If the version dir does not exist, create a new version dir in root dir.
        """
        version_root_dir: Path = Path(root_dir, version_obj.relative_root_dir)
        version_root_dir.mkdir(parents=True, exist_ok=True)
        LOG.info("Created new bundle version dir: %s", version_root_dir)
        return Path(version_root_dir, Path(file_obj.path).name)

    def include_file(self, file_obj: File, version_obj: Version) -> File:
        """Call the include version function to import related assets."""
        global_root_dir: Path = Path(self.get_root_dir())

        new_path: Path = self.get_included_path(
            root_dir=global_root_dir, version_obj=version_obj, file_obj=file_obj
        )
        if file_obj.to_archive:
            # calculate sha1 checksum if file is to be archived
            file_obj.checksum = HousekeeperAPI.checksum(file_obj.path)
        if new_path.exists():
            LOG.warning(
                f"Another file with identical included file path: {new_path} already exist. Skip linking of: {file_obj.path}"
            )
            file_obj.path = str(new_path).replace(f"{global_root_dir}/", "", 1)
            return file_obj
        # hardlink file to the internal structure
        os.link(file_obj.path, new_path)
        LOG.info(f"Linked file: {file_obj.path} -> {new_path}")
        file_obj.path = str(new_path).replace(f"{global_root_dir}/", "", 1)
        return file_obj

    def new_version(self, created_at: dt.datetime, expires_at: dt.datetime = None) -> Version:
        """Create a new bundle version."""
        return self._store.new_version(created_at, expires_at)

    def version(self, bundle: str, date: dt.datetime) -> Version:
        """Fetch a version."""
        LOG.info("Fetch version %s from bundle %s", date, bundle)
        return self._store.get_version_by_date_and_bundle_name(
            bundle_name=bundle, version_date=date
        )

    def last_version(self, bundle: str) -> Version:
        """Gets the latest version of a bundle."""
        LOG.debug(f"Fetch latest version from bundle {bundle}")
        return (
            self._store._get_query(table=Version)
            .join(Version.bundle)
            .filter(Bundle.name == bundle)
            .order_by(models.Version.created_at.desc())
            .first()
        )

    def get_latest_bundle_version(self, bundle_name: str) -> Optional[Version]:
        """Get the latest version of a Housekeeper bundle."""
        last_version: Version = self.last_version(bundle_name)
        if not last_version:
            LOG.warning(f"No bundle found for {bundle_name} in Housekeeper")
            return None
        LOG.debug(f"Found Housekeeper version object for {bundle_name}: {repr(last_version)}")
        return last_version

    def get_create_version(self, bundle_name: str) -> Version:
        """Returns the latest version of a bundle if it exists. If not creates a bundle and
        returns its version."""
        last_version: Version = self.last_version(bundle=bundle_name)
        if not last_version:
            LOG.info(f"Creating bundle for sample {bundle_name} in housekeeper")
            bundle_result: Tuple[Bundle, Version] = self.add_bundle(
                bundle_data={
                    "name": bundle_name,
                    "created_at": dt.datetime.now(),
                    "expires_at": None,
                    "files": [],
                }
            )
            last_version: Version = bundle_result[1]
        return last_version

    def new_tag(self, name: str, category: str = None):
        """Create a new tag."""
        return self._store.new_tag(name, category)

    def add_tag(self, name: str, category: str = None) -> models.Tag:
        """Add a tag to the database."""
        tag_obj = self._store.new_tag(name, category)
        self.add_commit(tag_obj)
        return tag_obj

    def get_tag(self, name: str) -> models.Tag:
        """Fetch a tag."""
        return self._store.get_tag(name)

    @staticmethod
    def get_tag_names_from_file(file: File) -> List[str]:
        """Fetch tag names for a file."""
        return [tag.name for tag in file.tags]

    def include(self, version_obj: Version):
        """Call the include version function to import related assets."""
        include_version(self.get_root_dir(), version_obj)
        version_obj.included_at = dt.datetime.now()

    def add_commit(self, obj):
        """Wrap method in Housekeeper Store."""
        self._store.session.add(obj)
        return self._store.session.commit()

    def commit(self):
        """Wrap method in Housekeeper Store."""
        return self._store.session.commit()

    def get_root_dir(self) -> str:
        """Returns the root dir of Housekeeper."""
        return self.root_dir

    @staticmethod
    def checksum(path) -> str:
        """Calculate the checksum."""
        return hk_checksum(path)

    def initialise_db(self):
        """Create all tables in the store."""
        self._store.create_all()

    def destroy_db(self):
        """Drop all tables in the store."""
        self._store.drop_all()

    def add_and_include_file_to_latest_version(
        self, bundle_name: str, file: Path, tags: list
    ) -> None:
        """Adds and includes a file in the latest version of a bundle."""
        version: Version = self.last_version(bundle_name)
        if not version:
            LOG.info(f"Bundle: {bundle_name} not found in Housekeeper")
            raise HousekeeperBundleVersionMissingError
        hk_file: File = self.add_file(version_obj=version, tags=tags, path=str(file.absolute()))
        self.include_file(version_obj=version, file_obj=hk_file)
        self.commit()

    def include_files_to_latest_version(self, bundle_name: str) -> None:
        """Include all files in the latest version on a bundle."""
        bundle_version: Version = self.get_latest_bundle_version(bundle_name=bundle_name)
        if not bundle_version:
            return None
        if bundle_version.included_at:
            LOG.info(
                f"Bundle: {bundle_name}, version: {bundle_version} already included at {bundle_version.included_at}"
            )
            return
        for hk_file in bundle_version.files:
            if not hk_file.is_included:
                try:
                    self.include_file(version_obj=bundle_version, file_obj=hk_file)
                except FileExistsError as error:
                    LOG.error(error)
                continue
            LOG.warning(
                f"File is already included in Housekeeper for bundle: {bundle_name}, version: {bundle_version}"
            )
        bundle_version.included_at = dt.datetime.now()
        self.commit()

    def get_file_from_latest_version(self, bundle_name: str, tags: Set[str]) -> Optional[File]:
        """Return a file in the latest version of a bundle."""
        version: Version = self.last_version(bundle=bundle_name)
        if not version:
            LOG.info(f"Bundle: {bundle_name} not found in Housekeeper")
            raise HousekeeperBundleVersionMissingError
        return self.files(version=version.id, tags=tags).first()

    def get_files_from_latest_version(self, bundle_name: str, tags: List[str]) -> Query:
        """Return files in the latest version of a bundle."""
        version: Version = self.last_version(bundle=bundle_name)
        if not version:
            LOG.info(f"Bundle: {bundle_name} not found in Housekeeper")
            raise HousekeeperBundleVersionMissingError
        return self.files(version=version.id, tags=tags)

    def is_fastq_or_spring_in_all_bundles(self, bundle_names: List[str]) -> bool:
        """Return whether or not all FASTQ/SPRING files are included for the given bundles."""
        sequencing_files_in_hk: Dict[str, bool] = {}
        if not bundle_names:
            return False
        for bundle_name in bundle_names:
            sequencing_files_in_hk[bundle_name] = False
            for tag in [SequencingFileTag.FASTQ, SequencingFileTag.SPRING_METADATA]:
                sample_file_in_hk: List[bool] = []
                hk_files: Optional[List[File]] = self.get_files_from_latest_version(
                    bundle_name=bundle_name, tags=[tag]
                )
                sample_file_in_hk += [True for hk_file in hk_files if hk_file.is_included]
                if sample_file_in_hk:
                    break
            sequencing_files_in_hk[bundle_name] = (
                all(sample_file_in_hk) if sample_file_in_hk else False
            )
        return all(sequencing_files_in_hk.values())

    def is_fastq_or_spring_on_disk_in_all_bundles(self, bundle_names: List[str]) -> bool:
        """Return whether or not all FASTQ/SPRING files are on disk for the given bundles."""
        sequencing_files_on_disk: Dict[str, bool] = {}
        if not bundle_names:
            return False
        for bundle_name in bundle_names:
            sequencing_files_on_disk[bundle_name] = False
            for tag in [SequencingFileTag.FASTQ, SequencingFileTag.SPRING_METADATA]:
                sample_file_on_disk: List[bool] = []
                hk_files: Optional[List[File]] = self.get_files_from_latest_version(
                    bundle_name=bundle_name, tags=[tag]
                )
                sample_file_on_disk += [
                    True for hk_file in hk_files if Path(hk_file.full_path).exists()
                ]
                if sample_file_on_disk:
                    break
            sequencing_files_on_disk[bundle_name] = (
                all(sample_file_on_disk) if sample_file_on_disk else False
            )
        return all(sequencing_files_on_disk.values())

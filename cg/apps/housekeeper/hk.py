""" Module to decouple cg code from Housekeeper code """

import logging
import os
from datetime import datetime
from pathlib import Path

from housekeeper.include import checksum as hk_checksum
from housekeeper.include import include_version
from housekeeper.store.database import create_all_tables, drop_all_tables, initialize_database
from housekeeper.store.models import Archive, Bundle, File, Tag, Version
from housekeeper.store.store import Store
from sqlalchemy.orm import Query

from cg.constants import SequencingFileTag
from cg.exc import (
    HousekeeperArchiveMissingError,
    HousekeeperBundleVersionMissingError,
    HousekeeperFileMissingError,
)

LOG = logging.getLogger(__name__)


class HousekeeperAPI:
    """API to decouple cg code from Housekeeper."""

    def __init__(self, config: dict) -> None:
        initialize_database(config["housekeeper"]["database"])
        self._store = Store(config["housekeeper"]["root"])
        self.root_dir: str = config["housekeeper"]["root"]

    def new_bundle(self, name: str, created_at: datetime = None) -> Bundle:
        """Create a new file bundle."""
        return self._store.new_bundle(name, created_at)

    def add_bundle(self, bundle_data) -> tuple[Bundle, Version]:
        """Build a new bundle version of files."""
        return self._store.add_bundle(bundle_data)

    def bundle(self, name: str) -> Bundle:
        """Fetch a bundle."""
        return self._store.get_bundle_by_name(bundle_name=name)

    def bundles(self) -> list[Bundle]:
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
        file.to_archive = value
        self.commit()

    def new_file(
        self, path: str, checksum: str = None, to_archive: bool = False, tags: list = None
    ) -> File:
        """Create a new file."""
        if tags is None:
            tags = []
        return self._store.new_file(path, checksum, to_archive, tags)

    def get_file(self, file_id: int) -> File | None:
        """Get a file based on file id."""
        LOG.info(f"Return file: {file_id}")
        file_obj: File = self._store.get_file_by_id(file_id=file_id)
        if not file_obj:
            LOG.info("file not found")
            return None
        return file_obj

    def delete_file(self, file_id: int) -> File | None:
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

    def add_file(
        self, path: str, version_obj: Version, tags: list, to_archive: bool = False
    ) -> File:
        """Add a file to the database."""
        if isinstance(tags, str):
            tags: list[str] = [tags]
        for tag_name in tags:
            if not self.get_tag(tag_name):
                self.add_tag(tag_name)

        new_file: File = self.new_file(
            path=str(Path(path).absolute()),
            to_archive=to_archive,
            tags=[self.get_tag(tag_name) for tag_name in tags],
        )

        new_file.version = version_obj
        self._store.session.add(new_file)
        return new_file

    def files(
        self,
        *,
        bundle: str = None,
        tags: set[str] = None,
        version: int = None,
        path: str = None,
    ) -> Query:
        """Fetch files."""
        return self._store.get_files(
            bundle_name=bundle, tag_names=tags, version_id=version, file_path=path
        )

    def get_file_insensitive_path(self, path: Path) -> File | None:
        """Returns a file in Housekeeper given any kind of path (absolute or relative)."""
        file: File = self.files(path=path.as_posix()).first()
        if not file:
            if path.is_absolute():
                file = self.files(path=str(path).replace(f"{self.root_dir}/", "")).first()
            else:
                file = self.files(path=f"{self.root_dir}/{path}").first()
        return file

    @staticmethod
    def get_files_from_version(version: Version, tags: set[str]) -> list[File]:
        """Return a list of files associated with the given version and tags."""
        LOG.debug(f"Getting files from version with tags {tags}")
        files: list[File] = []
        for file in list(version.files):
            file_tags = {tag.name for tag in file.tags}
            if tags.issubset(file_tags):
                LOG.debug(f"Found file {file}")
                files.append(file)
        if not files:
            LOG.warning(f"Could not find any files matching the tags {tags}")
        return files

    @staticmethod
    def get_file_from_version(version: Version, tags: set[str]) -> File | None:
        """Return the first file matching the given tags."""
        files: list[File] = HousekeeperAPI.get_files_from_version(version=version, tags=tags)
        return next((file for file in files), None)

    @staticmethod
    def get_latest_file_from_version(version: Version, tags: set[str]) -> File | None:
        """Return the latest file from Housekeeper given its version and tags."""
        files: list[File] = HousekeeperAPI.get_files_from_version(version=version, tags=tags)
        return sorted(files, key=lambda file_obj: file_obj.id)[-1] if files else None

    def rollback(self):
        """Wrap method in Housekeeper Store."""
        return self._store.session.rollback()

    def get_files(self, bundle: str, tags: list | None = None, version: int | None = None) -> Query:
        """Get all the files in housekeeper, optionally filtered by bundle and/or tags and/or
        version.
        """
        return self._store.get_files(bundle_name=bundle, tag_names=tags, version_id=version)

    def get_latest_file(
        self, bundle: str, tags: list | None = None, version: int | None = None
    ) -> File | None:
        """Return latest file from Housekeeper, filtered by bundle and/or tags and/or version."""
        files: Query = self._store.get_files(bundle_name=bundle, tag_names=tags, version_id=version)
        return files.order_by(File.id.desc()).first()

    def get_latest_file_strict(
        self, bundle: str, tags: list | None = None, version: int | None = None
    ) -> File:
        """
        Return latest file from Housekeeper, filtered by bundle and/or tags and/or version.
        Raises:
            HousekeeperFileMissingError if no file is found.
        """
        files: Query = self._store.get_files(bundle_name=bundle, tag_names=tags, version_id=version)
        latest_file: File | None = files.order_by(File.id.desc()).first()
        if not latest_file:
            raise HousekeeperFileMissingError(
                f"No file matching bundle {bundle}, version {version} with tags {tags}"
            )
        else:
            return latest_file

    def check_bundle_files(
        self,
        bundle_name: str,
        file_paths: list[Path],
        last_version: Version,
        tags: list | None = None,
    ) -> list[Path]:
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
        LOG.info(f"Created new bundle version dir: {version_root_dir}")
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

    def new_version(self, created_at: datetime, expires_at: datetime = None) -> Version:
        """Create a new bundle version."""
        return self._store.new_version(created_at, expires_at)

    def get_version_by_id(self, version_id: int) -> Version:
        """Return a version given its database ID."""
        return self._store.get_version_by_id(version_id=version_id)

    def last_version(self, bundle: str) -> Version:
        """Gets the latest version of a bundle."""
        LOG.debug(f"Fetch latest version from bundle {bundle}")
        return (
            self._store._get_query(table=Version)
            .join(Version.bundle)
            .filter(Bundle.name == bundle)
            .order_by(Version.created_at.desc())
            .first()
        )

    def get_non_archived_spring_files(
        self, tags: list[str] | None = None, limit: int = None
    ) -> list[File]:
        """Return all spring files which are not marked as archived in Housekeeper."""
        return self._store.get_non_archived_files(
            tag_names=tags + [SequencingFileTag.SPRING] if tags else [SequencingFileTag.SPRING],
            limit=limit,
        )

    def get_latest_bundle_version(self, bundle_name: str) -> Version | None:
        """Get the latest version of a Housekeeper bundle."""
        last_version: Version = self.last_version(bundle_name)
        if not last_version:
            LOG.debug(f"No bundle found for {bundle_name} in Housekeeper")
            return None
        LOG.debug(f"Found Housekeeper version object for {bundle_name}: {repr(last_version)}")
        return last_version

    def get_or_create_version(self, bundle_name: str) -> Version:
        """Returns the latest version of a bundle if it exists. If not creates a bundle and
        returns its version."""
        last_version: Version = self.last_version(bundle=bundle_name)
        if not last_version:
            LOG.info(f"Creating bundle for sample {bundle_name} in housekeeper")
            bundle_result: tuple[Bundle, Version] = self.add_bundle(
                bundle_data={
                    "name": bundle_name,
                    "created_at": datetime.now(),
                    "expires_at": None,
                    "files": [],
                }
            )
            last_version: Version = bundle_result[1]
        return last_version

    def new_tag(self, name: str, category: str = None):
        """Create a new tag."""
        return self._store.new_tag(name, category)

    def add_tag(self, name: str, category: str = None) -> Tag:
        """Add a tag to the database."""
        tag_obj = self._store.new_tag(name, category)
        self.add_commit(tag_obj)
        return tag_obj

    def get_tag(self, name: str) -> Tag:
        """Fetch a tag."""
        return self._store.get_tag(name)

    @staticmethod
    def get_tag_names_from_file(file: File) -> list[str]:
        """Fetch tag names for a file."""
        return [tag.name for tag in file.tags]

    def include(self, version_obj: Version):
        """Call the include version function to import related assets."""
        include_version(self.get_root_dir(), version_obj)
        version_obj.included_at = datetime.now()

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
        create_all_tables()

    def destroy_db(self):
        """Drop all tables in the store."""
        drop_all_tables()

    def add_and_include_file_to_latest_version(
        self, bundle_name: str, file: Path, tags: list
    ) -> None:
        """Adds and includes a file in the latest version of a bundle."""
        version: Version = self.get_or_create_version(bundle_name)
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
        bundle_version.included_at = datetime.now()
        self.commit()

    def get_file_from_latest_version(self, bundle_name: str, tags: set[str]) -> File | None:
        """Return a file in the latest version of a bundle."""
        version: Version = self.last_version(bundle=bundle_name)
        if not version:
            LOG.warning(f"Bundle: {bundle_name} not found in Housekeeper")
            raise HousekeeperBundleVersionMissingError
        return self.files(version=version.id, tags=tags).first()

    def get_files_from_latest_version(
        self, bundle_name: str, tags: list[str] | None = None
    ) -> list[File] | None:
        """Return files in the latest version of a bundle.

        Raises HousekeeperBundleVersionMissingError:
        - When no version was found for the given bundle
        """
        version: Version = self.last_version(bundle=bundle_name)
        if not version:
            LOG.warning(f"Bundle: {bundle_name} not found in Housekeeper")
            raise HousekeeperBundleVersionMissingError
        return self.files(version=version.id, tags=tags).all()

    def get_non_archived_files_for_bundle(
        self, bundle_name: str, tags: list | None = None
    ) -> list[File]:
        """Returns all non-archived_files from a given bundle, tagged with the given tags"""
        return self._store.get_non_archived_files_for_bundle(
            bundle_name=bundle_name, tags=tags or []
        )

    def get_archived_files_for_bundle(
        self, bundle_name: str, tags: list | None = None
    ) -> list[File]:
        """Returns all archived_files from a given bundle, tagged with the given tags"""
        LOG.debug(f"Getting archived files for bundle {bundle_name}")
        return self._store.get_archived_files_for_bundle(bundle_name=bundle_name, tags=tags or [])

    def get_archived_files_not_being_retrieved_for_bundle(
        self, bundle_name: str, tags: list | None = None
    ) -> list[File]:
        """Returns archived files from a bundle, excluding files currently being retrieved."""
        LOG.debug(f"Getting archived files which are not being retrieved for bundle {bundle_name}.")
        return self._store.get_archived_files_for_bundle_excluding_ongoing_retrievals(
            bundle_name=bundle_name, tags=tags or []
        )

    def add_archives(self, files: list[File], archive_task_id: int) -> None:
        """Creates an archive object for the given files, and adds the archive task id to them."""
        for file in files:
            file_id: int = file.id
            LOG.info(
                f"Adding an archive to file {file_id} with archiving task id {archive_task_id}"
            )
            archive: Archive = self._store.create_archive(
                file_id=file_id, archiving_task_id=archive_task_id
            )
            self._store.session.add(archive)
        self.commit()

    def set_archive_retrieved_at(self, file_id: int, retrieval_task_id: int):
        """Sets the retrieved_at value for an Archive entry. Raises a ValueError if the given retrieval task id
        is not found in Housekeeper."""
        archive: Archive = self._store.get_file_by_id(file_id).archive
        if archive.retrieval_task_id != retrieval_task_id:
            raise ValueError(
                f"Retrieval task id did not match database entry. Given task id was {retrieval_task_id}, "
                f"while retrieval task id in Housekeeper is {archive.retrieval_task_id}."
            )
        self._store.update_retrieval_time_stamp(archive=archive)
        self.commit()

    def set_archive_archived_at(self, file_id: int, archiving_task_id: int):
        """Sets the archived_at value for an Archive entry. Raises a ValueError if the given archiving task id
        is not found in Housekeeper."""
        archive: Archive = self._store.get_file_by_id(file_id).archive
        if archive.archiving_task_id != archiving_task_id:
            raise ValueError(
                f"Archiving task id did not match database entry. Given task id was {archiving_task_id}, "
                f"while archiving task id in Housekeeper is {archive.archiving_task_id}."
            )
        self._store.update_archiving_time_stamp(archive=archive)

    def set_archive_retrieval_task_id(self, file_id: int, retrieval_task_id: int) -> None:
        """Sets the retrieval_task_id for an Archive entry. Raises a ValueError if the given retrieval task id
        is not found in Housekeeper."""
        archive: Archive = self._store.get_file_by_id(file_id).archive
        if not archive:
            raise ValueError(f"No Archive entry found for file with id {file_id}.")
        self._store.update_retrieval_task_id(archive=archive, retrieval_task_id=retrieval_task_id)
        self.commit()

    def get_sample_sheets_from_latest_version(self, flow_cell_id: str) -> list[File]:
        """Returns the files tagged with 'samplesheet' for the given bundle."""
        try:
            sample_sheet_files: list[File] = self.get_files_from_latest_version(
                bundle_name=flow_cell_id, tags=[flow_cell_id, SequencingFileTag.SAMPLE_SHEET]
            )
        except HousekeeperBundleVersionMissingError:
            sample_sheet_files = []
        return sample_sheet_files

    def get_sample_sheet_path(self, flow_cell_id: str) -> Path:
        """Returns the sample sheet path for the flow cell."""
        sample_sheet_files: list[File] = self.get_sample_sheets_from_latest_version(flow_cell_id)
        if not sample_sheet_files:
            LOG.error(f"Sample sheet file for flowcell {flow_cell_id} not found in Housekeeper!")
            raise HousekeeperFileMissingError
        return Path(sample_sheet_files[0].full_path)

    def file_exists_in_latest_version_for_bundle(self, file_path: Path, bundle_name: str) -> bool:
        """Check if a file exists in the latest version for bundle."""
        latest_version: Version = self.get_latest_bundle_version(bundle_name)
        return any(
            file_path.name == Path(bundle_file.path).name for bundle_file in latest_version.files
        )

    def add_file_to_bundle_if_non_existent(
        self, file_path: Path, bundle_name: str, tag_names: list[str]
    ) -> None:
        """Add file to Housekeeper if it has not already been added."""
        if not file_path.exists():
            LOG.warning(f"File does not exist: {file_path}")
            return

        if not self.file_exists_in_latest_version_for_bundle(
            file_path=file_path, bundle_name=bundle_name
        ):
            self.add_and_include_file_to_latest_version(
                bundle_name=bundle_name,
                file=file_path,
                tags=tag_names,
            )
            LOG.info(f"File added to Housekeeper bundle {bundle_name}")
        else:
            LOG.info(f"Bundle {bundle_name} already has a file with the same name as {file_path}")

    def add_tags_if_non_existent(self, tag_names: list[str]) -> None:
        """Ensure that tags exist in Housekeeper."""
        for tag_name in tag_names:
            if self.get_tag(name=tag_name) is None:
                self.add_tag(name=tag_name)

    def add_bundle_and_version_if_non_existent(self, bundle_name: str) -> None:
        """Add bundle if it does not exist."""
        if not self.bundle(name=bundle_name):
            self.create_new_bundle_and_version(name=bundle_name)
        else:
            LOG.debug(f"Bundle with name {bundle_name} already exists")

    def create_bundle_and_add_file_with_tags(
        self,
        bundle_name: str,
        file_path: Path,
        tags: list[str],
    ) -> None:
        """Add a file path with tags to a bundle and version in Housekeeper."""
        self.add_bundle_and_version_if_non_existent(bundle_name)
        self.add_tags_if_non_existent([bundle_name])
        self.add_file_to_bundle_if_non_existent(
            file_path=file_path,
            bundle_name=bundle_name,
            tag_names=tags,
        )

    def get_archive_entries(
        self, archival_task_id: int = None, retrieval_task_id: int = None
    ) -> list[Archive]:
        """Returns all archives matching the provided task ids. If no task ids are provided, all archive entries are
        returned. If only an archival_task_id is provided, filtering is only done on that parameter and vice versa
        with retrieval_task_id.
        """
        return self._store.get_archives(
            archival_task_id=archival_task_id, retrieval_task_id=retrieval_task_id
        )

    def set_archived_at(self, archival_task_id: int) -> None:
        """Sets archived_at to the current time for archive entries with matching archival task id.
        Raises:
                HousekeeperArchiveMissingError if no Archive entries match the given retrieval task id.
        """
        archive_entries: list[Archive] = self.get_archive_entries(archival_task_id=archival_task_id)
        if not archive_entries:
            raise HousekeeperArchiveMissingError(
                f"Could not find any archives with archival_task_id {archival_task_id}"
            )
        for archive in archive_entries:
            self.set_archive_archived_at(
                archiving_task_id=archival_task_id, file_id=archive.file_id
            )
        self.commit()

    def set_retrieved_at(self, retrieval_task_id: int) -> None:
        """Sets retrieved_at to the current time for archive entries with matching archival task id.
        Raises:
                HousekeeperArchiveMissingError if no Archive entries match the given retrieval task id.
        """
        archive_entries: list[Archive] = self.get_archive_entries(
            retrieval_task_id=retrieval_task_id
        )
        if not archive_entries:
            raise HousekeeperArchiveMissingError(
                f"Could not find any archives with retrieval_task_id {retrieval_task_id}"
            )
        for archive in archive_entries:
            self.set_archive_retrieved_at(
                retrieval_task_id=retrieval_task_id, file_id=archive.file_id
            )
        self.commit()

    def get_ongoing_archivals(self) -> list[Archive]:
        return self._store.get_ongoing_archivals()

    def get_ongoing_retrievals(self) -> list[Archive]:
        return self._store.get_ongoing_retrievals()

    def delete_archives(self, archival_task_id: int):
        archives_to_delete: list[Archive] = self.get_archive_entries(
            archival_task_id=archival_task_id
        )
        for archive in archives_to_delete:
            self._store.session.delete(archive)
        self._store.session.commit()

    def update_archive_retrieved_at(
        self, old_retrieval_job_id: int, new_retrieval_job_id: int | None
    ):
        archives_to_update: list[Archive] = self.get_archive_entries(
            retrieval_task_id=old_retrieval_job_id
        )
        for archive in archives_to_update:
            archive.retrieval_task_id = new_retrieval_job_id
        self._store.session.commit()

    def get_spring_files_retrieved_before(self, date: datetime):
        return self._store.get_files_retrieved_before(date, tag_names=[SequencingFileTag.SPRING])

    def reset_retrieved_archive_data(self, files_to_reset: list[File]):
        """Resets 'retrieval_task_id' and 'retrieved_at' for all files' corresponding archive entries"""
        for file in files_to_reset:
            LOG.debug(f"Resetting retrieval data for file {file.path}")
            file.archive.retrieval_task_id = None
            file.archive.retrieved_at = None
        self.commit()

    @staticmethod
    def get_files_containing_tags(files: list[File], tags: list[set[str]]) -> list[File]:
        """Return files containing specified tags."""
        filtered_files: list[File] = []
        for file in files:
            file_tags: set[str] = {tag.name for tag in file.tags}
            if any(tag.issubset(file_tags) for tag in tags):
                filtered_files.append(file)
        return filtered_files

    @staticmethod
    def get_files_without_excluded_tags(files: list[File], excluded_tags: list[str]) -> list[File]:
        """Return files without specified tags."""
        filtered_files: list[File] = []
        for file in files:
            file_tags: list[str] = [tag.name for tag in file.tags]
            if not any(excluded_tag in file_tags for excluded_tag in excluded_tags):
                filtered_files.append(file)
        return filtered_files

    def get_files_from_latest_version_containing_tags(
        self, bundle_name: str, tags: list[set[str]], excluded_tags: list[str] | None = None
    ) -> list[File]:
        """
        Return files from the latest version of a bundle matching provided tags. Files containing
        any tag sets specified in the excluded_tags list will be excluded from the output.
        """
        files: list[File] = self.get_files_from_latest_version(bundle_name=bundle_name)
        filtered_files: list[File] = self.get_files_containing_tags(files=files, tags=tags)
        if excluded_tags:
            filtered_files: list[File] = self.get_files_without_excluded_tags(
                files=filtered_files, excluded_tags=excluded_tags
            )
        return filtered_files

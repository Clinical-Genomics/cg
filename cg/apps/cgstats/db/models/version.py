from sqlalchemy import Column, UniqueConstraint, types

from .base import Model


class Version(Model):

    __table_args__ = (
        UniqueConstraint("name", "major", "minor", "patch", name="name_major_minor_patch_uc"),
    )

    version_id = Column(types.Integer, primary_key=True)
    name = Column(types.String(255))
    major = Column(types.Integer)
    minor = Column(types.Integer)
    patch = Column(types.Integer)
    comment = Column(types.String(255))
    time = Column(types.DateTime, nullable=False)

    @staticmethod
    def check(dbname: str, ver: str) -> bool:
        """Checks version of database against dbname and version

        [normally from the config file]

        Args:
          dbname (str): database name as stored in table version
          ver (str): version string in the format major.minor.patch

        Returns:
          True: if identical
        """
        version: Version = Version.get_version()
        if version is None:
            return False
        ver_string = "{0}.{1}.{2}".format(
            str(version.major), str(version.minor), str(version.patch)
        )
        return (ver_string == ver) and (dbname == version.name)

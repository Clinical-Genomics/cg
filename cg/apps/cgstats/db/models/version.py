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

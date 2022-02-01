from typing import Optional

from sqlalchemy import Column, ForeignKey, UniqueConstraint, orm, types
from sqlalchemy.orm.exc import NoResultFound

from .base import Model


class Project(Model):

    project_id = Column(types.Integer, primary_key=True)
    projectname = Column(types.String(255), nullable=False)
    comment = Column(types.Text)
    time = Column(types.DateTime, nullable=False)

    samples = orm.relationship("Sample", cascade="all", backref=orm.backref("project"))

    def __repr__(self):
        return "{self.__class__.__name__}: {self.project_id}".format(self=self)

    @staticmethod
    def exists(project_name: str) -> Optional[int]:
        """Checks if the Project entry already exists"""
        try:
            project: Project = Project.query.filter_by(projectname=project_name).one()
            return project.project_id
        except NoResultFound:
            return None

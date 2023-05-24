from sqlalchemy import Column, orm, types

from .base import Model


class Project(Model):
    project_id = Column(types.Integer, primary_key=True)
    projectname = Column(types.String(255), nullable=False)
    comment = Column(types.Text)
    time = Column(types.DateTime, nullable=False)

    samples = orm.relationship("Sample", cascade="all", backref=orm.backref("project"))

    def __repr__(self):
        return "{self.__class__.__name__}: {self.project_id}".format(self=self)

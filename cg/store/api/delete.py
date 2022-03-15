"""Handler to delete data objects"""

from cg.store import models
from cg.store.api.base import BaseHandler


class DeleteDataHandler(BaseHandler):
    """Contains methods to delete business data model instances"""

    def delete_flowcell(self, flowcell_name: str):
        flowcell: models.Flowcell = self.Flowcell.query.filter(
            models.Flowcell.name == flowcell_name
        ).first()
        if flowcell:
            flowcell.delete()
            flowcell.flush()
            self.commit()

import json
from datetime import datetime

from alchy import ModelBase, make_declarative_base


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


class JsonModel(ModelBase):
    def to_json(self, pretty: bool = False):
        """Serialize to JSON.

        Handle DateTime objects.
        """
        kwargs = dict(indent=4, sort_keys=True) if pretty else dict()
        return json.dumps(self.to_dict(), default=json_serial, **kwargs)


Model = make_declarative_base(Base=JsonModel)

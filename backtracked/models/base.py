from collections import OrderedDict

class Model:
    def __init__(self, client, *args):
        self.client = client

    @classmethod
    def from_data(cls, client, data: dict):
        cls(client, data)

class BaseCollection:
    def add(self, obj):
        if hasattr(obj, "id"):
            self[obj.id] = obj

class Collection(dict, BaseCollection):
    def __init__(self):
        super().__init__()

class OrderedCollection(OrderedDict):
    def __init__(self):
        super().__init__()

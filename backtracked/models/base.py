from collections import OrderedDict

class Model:
    def __init__(self, client, *args):
        self.client = client

    @classmethod
    def from_data(cls, client, data: dict):
        cls(client, data)

    def __getitem__(self, item):
        return getattr(self, item, None)

    def __str__(self):
        return f"{self.__class__.__name__} object: {self.__dict__}"

class BaseCollection:
    def add(self, obj):
        pass

class Collection(dict, BaseCollection):
    def __init__(self):
        super().__init__()

    def add(self, obj):
        if hasattr(obj, "id"):
            self[obj.id] = obj

class OrderedCollection(OrderedDict, BaseCollection):
    def __init__(self):
        super().__init__()

    def add(self, obj):
        if hasattr(obj, "id"):
            self[obj.id] = obj

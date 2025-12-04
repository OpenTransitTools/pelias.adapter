from pyramid.interfaces import IMultiDict
from zope.interface import implementer


@implementer(IMultiDict)
class TestMultiDict(dict):
    """A simple implementation of a multi-dict."""

    def add(self, key, value):
        """Add a value to the list of values for the given key."""
        if key in self:
            current_value = self[key]
            if isinstance(current_value, list):
                current_value.append(value)
            else:
                self[key] = [current_value, value]
        else:
            self[key] = value

    def getall(self, key):
        """Get all values for the given key as a list."""
        if key in self:
            value = self[key]
            if isinstance(value, list):
                return value
            else:
                return [value]
        return []

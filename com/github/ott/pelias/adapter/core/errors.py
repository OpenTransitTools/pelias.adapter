class PeliasAdapterError(Exception):
    """Base class for all Pelias Adapter exceptions."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message

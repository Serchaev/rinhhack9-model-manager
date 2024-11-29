class ObjectNotFound(Exception):
    """Raised when the object not found"""

    pass


class ServiceUnavailable(Exception):
    """Raised when the service is unavailable"""

    pass


class OutDiskSpace(Exception):
    """Raised when out of disk space"""

    pass

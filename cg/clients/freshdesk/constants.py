from enum import IntEnum


class EndPoints:
    TICKETS = "/api/v2/tickets"


class Status(IntEnum):
    OPEN = 2
    PENDING = 3
    RESOLVED = 4
    CLOSED = 5


class Source:
    EMAIL = 1
    PORTAL = 2


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

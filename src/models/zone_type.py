from enum import Enum


class ZoneType(str, Enum):
    """Enumerates the supported zone behaviors."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

from .zone_type import ZoneType


class Zone:
    """Represents a zone node in the drone graph."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: str = "none",
        max_drones: int = 1,
    ) -> None:
        """Initializes a zone.

        Args:
            name: Unique zone name.
            x: Horizontal coordinate.
            y: Vertical coordinate.
            zone_type: Zone behavior category.
            color: Visual color name.
            max_drones: Simultaneous occupancy capacity.

        Returns:
            None.
        """
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones

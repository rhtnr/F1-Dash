"""Track status enumeration."""

from enum import Enum


class TrackStatus(str, Enum):
    """F1 track status flags."""

    GREEN = "1"
    YELLOW = "2"
    SC = "4"  # Safety Car
    RED = "5"
    VSC = "6"  # Virtual Safety Car
    VSC_ENDING = "7"

    @classmethod
    def from_fastf1(cls, status: str | None) -> "TrackStatus":
        """Convert FastF1 track status to enum."""
        if status is None:
            return cls.GREEN
        # FastF1 can return combined statuses like "14" (Green + SC)
        # We take the highest priority status
        status_str = str(status)
        if "5" in status_str:
            return cls.RED
        if "4" in status_str:
            return cls.SC
        if "6" in status_str:
            return cls.VSC
        if "7" in status_str:
            return cls.VSC_ENDING
        if "2" in status_str:
            return cls.YELLOW
        return cls.GREEN

    @property
    def display_name(self) -> str:
        """Get human-readable status name."""
        names = {
            self.GREEN: "Green Flag",
            self.YELLOW: "Yellow Flag",
            self.SC: "Safety Car",
            self.RED: "Red Flag",
            self.VSC: "Virtual Safety Car",
            self.VSC_ENDING: "VSC Ending",
        }
        return names.get(self, "Unknown")

    @property
    def color(self) -> str:
        """Get status indicator color."""
        colors = {
            self.GREEN: "#00FF00",
            self.YELLOW: "#FFFF00",
            self.SC: "#FFA500",
            self.RED: "#FF0000",
            self.VSC: "#FFA500",
            self.VSC_ENDING: "#90EE90",
        }
        return colors.get(self, "#FFFFFF")

    @property
    def affects_lap_time(self) -> bool:
        """Check if this status typically affects lap times."""
        return self not in (self.GREEN,)

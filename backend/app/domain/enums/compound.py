"""Tire compound enumeration."""

from enum import Enum


class TireCompound(str, Enum):
    """F1 tire compound types."""

    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"
    UNKNOWN = "UNKNOWN"
    TEST_UNKNOWN = "TEST_UNKNOWN"

    @classmethod
    def from_fastf1(cls, compound: str | None) -> "TireCompound":
        """Convert FastF1 compound string to enum."""
        if compound is None:
            return cls.UNKNOWN
        try:
            return cls(compound.upper())
        except ValueError:
            return cls.UNKNOWN

    @property
    def color(self) -> str:
        """Get the official tire compound color."""
        colors = {
            self.SOFT: "#FF3333",
            self.MEDIUM: "#FCD500",
            self.HARD: "#EBEBEB",
            self.INTERMEDIATE: "#43B02A",
            self.WET: "#0067AD",
            self.UNKNOWN: "#888888",
            self.TEST_UNKNOWN: "#888888",
        }
        return colors.get(self, "#888888")

    @property
    def short_name(self) -> str:
        """Get single letter abbreviation."""
        return self.value[0] if self != self.UNKNOWN else "?"

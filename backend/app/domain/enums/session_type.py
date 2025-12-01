"""Session type enumeration."""

from enum import Enum


class SessionType(str, Enum):
    """F1 session types."""

    PRACTICE_1 = "FP1"
    PRACTICE_2 = "FP2"
    PRACTICE_3 = "FP3"
    QUALIFYING = "Q"
    SPRINT_SHOOTOUT = "SS"
    SPRINT = "S"
    RACE = "R"

    @classmethod
    def from_fastf1(cls, session_name: str) -> "SessionType":
        """Convert FastF1 session name to enum."""
        mapping = {
            "Practice 1": cls.PRACTICE_1,
            "Practice 2": cls.PRACTICE_2,
            "Practice 3": cls.PRACTICE_3,
            "Qualifying": cls.QUALIFYING,
            "Sprint Shootout": cls.SPRINT_SHOOTOUT,
            "Sprint Qualifying": cls.SPRINT_SHOOTOUT,
            "Sprint": cls.SPRINT,
            "Race": cls.RACE,
            "FP1": cls.PRACTICE_1,
            "FP2": cls.PRACTICE_2,
            "FP3": cls.PRACTICE_3,
            "Q": cls.QUALIFYING,
            "SQ": cls.SPRINT_SHOOTOUT,
            "SS": cls.SPRINT_SHOOTOUT,
            "S": cls.SPRINT,
            "R": cls.RACE,
        }
        return mapping.get(session_name, cls.RACE)

    @property
    def display_name(self) -> str:
        """Get human-readable session name."""
        names = {
            self.PRACTICE_1: "Practice 1",
            self.PRACTICE_2: "Practice 2",
            self.PRACTICE_3: "Practice 3",
            self.QUALIFYING: "Qualifying",
            self.SPRINT_SHOOTOUT: "Sprint Shootout",
            self.SPRINT: "Sprint",
            self.RACE: "Race",
        }
        return names.get(self, self.value)

    @property
    def is_race(self) -> bool:
        """Check if this is a race session (Race or Sprint)."""
        return self in (self.RACE, self.SPRINT)

"""Team domain model."""

from pydantic import BaseModel, Field


class Team(BaseModel):
    """Represents an F1 team/constructor."""

    id: str = Field(..., description="Team identifier")
    name: str = Field(..., description="Full team name")
    short_name: str = Field(..., description="Short team name")
    color: str = Field(..., description="Team color hex code")
    country: str | None = Field(None, description="Team headquarters country")

    model_config = {"frozen": True}

    @classmethod
    def create_id(cls, name: str) -> str:
        """Create a team ID from name."""
        # Normalize team name to create consistent ID
        return name.lower().replace(" ", "_").replace("-", "_")


# Predefined team colors (2024 season)
TEAM_COLORS: dict[str, str] = {
    "Red Bull Racing": "#3671C6",
    "Ferrari": "#E80020",
    "Mercedes": "#27F4D2",
    "McLaren": "#FF8000",
    "Aston Martin": "#229971",
    "Alpine": "#FF87BC",
    "Williams": "#64C4FF",
    "AlphaTauri": "#6692FF",
    "RB": "#6692FF",
    "Alfa Romeo": "#C92D4B",
    "Kick Sauber": "#52E252",
    "Sauber": "#52E252",
    "Haas F1 Team": "#B6BABD",
}


def get_team_color(team_name: str) -> str:
    """Get team color by name, with fallback."""
    for name, color in TEAM_COLORS.items():
        if name.lower() in team_name.lower() or team_name.lower() in name.lower():
            return color
    return "#888888"

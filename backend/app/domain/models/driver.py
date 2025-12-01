"""Driver domain model."""

from pydantic import BaseModel, Field


class Driver(BaseModel):
    """Represents an F1 driver."""

    id: str = Field(..., description="Driver abbreviation (e.g., 'VER', 'HAM')")
    number: int = Field(..., description="Car number")
    full_name: str = Field(..., description="Full name")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    team_id: str = Field(..., description="Team identifier")
    team_name: str = Field(..., description="Team name")
    team_color: str = Field(..., description="Team color hex code")
    country_code: str | None = Field(None, description="Country code (e.g., 'NED')")
    headshot_url: str | None = Field(None, description="URL to driver headshot")

    model_config = {"frozen": True}

    @property
    def display_name(self) -> str:
        """Get formatted display name."""
        return f"{self.first_name[0]}. {self.last_name}"

    @classmethod
    def create_id(cls, abbreviation: str) -> str:
        """Create a driver ID from abbreviation."""
        return abbreviation.upper()

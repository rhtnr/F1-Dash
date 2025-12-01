"""Weather domain model."""

from datetime import datetime

from pydantic import BaseModel, Field


class Weather(BaseModel):
    """Weather conditions at a point in time during a session."""

    session_id: str = Field(..., description="Parent session ID")
    timestamp: datetime = Field(..., description="Timestamp of measurement")

    # Temperature
    air_temp: float = Field(..., description="Air temperature (Celsius)")
    track_temp: float = Field(..., description="Track temperature (Celsius)")

    # Conditions
    humidity: float = Field(..., ge=0, le=100, description="Humidity (%)")
    pressure: float = Field(..., description="Air pressure (mbar)")
    wind_speed: float = Field(..., ge=0, description="Wind speed (m/s)")
    wind_direction: int = Field(..., ge=0, lt=360, description="Wind direction (degrees)")

    # Precipitation
    rainfall: bool = Field(False, description="Is it raining")

    model_config = {"frozen": True}

    @property
    def is_wet(self) -> bool:
        """Check if conditions are wet."""
        return self.rainfall

    @property
    def wind_direction_name(self) -> str:
        """Get wind direction as compass direction."""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = round(self.wind_direction / 45) % 8
        return directions[index]


class SessionWeatherSummary(BaseModel):
    """Summary of weather conditions for a session."""

    session_id: str = Field(..., description="Session ID")

    # Temperature ranges
    air_temp_min: float = Field(..., description="Minimum air temperature")
    air_temp_max: float = Field(..., description="Maximum air temperature")
    air_temp_avg: float = Field(..., description="Average air temperature")
    track_temp_min: float = Field(..., description="Minimum track temperature")
    track_temp_max: float = Field(..., description="Maximum track temperature")
    track_temp_avg: float = Field(..., description="Average track temperature")

    # Conditions
    had_rain: bool = Field(False, description="Did it rain during session")
    humidity_avg: float = Field(..., description="Average humidity")

    # Wind
    wind_speed_avg: float = Field(..., description="Average wind speed")
    wind_speed_max: float = Field(..., description="Maximum wind speed")

    model_config = {"frozen": True}

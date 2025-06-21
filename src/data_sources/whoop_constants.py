"""Constants for Whoop API."""

# Sport IDs observed in user data
SPORT_NAMES = {
    18: "Rowing",
    63: "Walking",
    65: "Elliptical",
    66: "Stairmaster",
    123: "Strength",
}


def get_sport_name(sport_id: int) -> str:
    """Get sport name from sport ID."""
    return SPORT_NAMES.get(sport_id, f"Unknown Sport ({sport_id})")

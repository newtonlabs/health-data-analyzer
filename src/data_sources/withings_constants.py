"""Constants for Withings API integration."""
from typing import Dict, Any, List

# API endpoints
BASE_URL = "https://wbsapi.withings.net"
AUTH_URL = "https://account.withings.com/oauth2_user/authorize2"
TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"

# Measurement types
class MeasurementType:
    """Withings measurement types."""
    WEIGHT = 1
    HEIGHT = 4
    FAT_FREE_MASS = 5
    FAT_RATIO = 6
    FAT_MASS_WEIGHT = 8
    DIASTOLIC_BLOOD_PRESSURE = 9
    SYSTOLIC_BLOOD_PRESSURE = 10
    HEART_RATE = 11
    TEMPERATURE = 12
    SP02 = 54
    BODY_TEMPERATURE = 71
    SKIN_TEMPERATURE = 73
    MUSCLE_MASS = 76
    HYDRATION = 77
    BONE_MASS = 88
    PULSE_WAVE_VELOCITY = 91

# No activity or sleep types needed for weight-only implementation

def get_measurement_name(measurement_type: int) -> str:
    """Get the name of a measurement type.
    
    Args:
        measurement_type: Measurement type ID
        
    Returns:
        Name of the measurement type
    """
    measurement_names = {
        MeasurementType.WEIGHT: "Weight",
        MeasurementType.HEIGHT: "Height",
        MeasurementType.FAT_FREE_MASS: "Fat Free Mass",
        MeasurementType.FAT_RATIO: "Fat Ratio",
        MeasurementType.FAT_MASS_WEIGHT: "Fat Mass Weight",
        MeasurementType.DIASTOLIC_BLOOD_PRESSURE: "Diastolic Blood Pressure",
        MeasurementType.SYSTOLIC_BLOOD_PRESSURE: "Systolic Blood Pressure",
        MeasurementType.HEART_RATE: "Heart Rate",
        MeasurementType.TEMPERATURE: "Temperature",
        MeasurementType.SP02: "SpO2",
        MeasurementType.BODY_TEMPERATURE: "Body Temperature",
        MeasurementType.SKIN_TEMPERATURE: "Skin Temperature",
        MeasurementType.MUSCLE_MASS: "Muscle Mass",
        MeasurementType.HYDRATION: "Hydration",
        MeasurementType.BONE_MASS: "Bone Mass",
        MeasurementType.PULSE_WAVE_VELOCITY: "Pulse Wave Velocity"
    }
    return measurement_names.get(measurement_type, f"Unknown ({measurement_type})")

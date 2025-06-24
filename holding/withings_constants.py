"""Constants for Withings API integration."""


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

# Configuration Tracking

## Purpose
Track which configuration settings actually exist in the codebase vs speculative features to prevent unused code accumulation.

## Current Configuration (Minimal - Actually Used)

### ✅ STRENGTH_ACTIVITIES
- **Source**: `app_config.py` → `ANALYSIS_STRENGTH_ACTIVITIES`
- **Used by**: Analysis processors for activity classification
- **Values**: `["Strength", "Weightlifting"]`

### ✅ CALORIC_TARGETS  
- **Source**: `app_config.py` → `REPORTING_CALORIC_TARGETS`
- **Used by**: Reporting for target lines on charts
- **Values**: `{"strength_day": 2400, "rest_day": 1800}`

### ✅ RECOVERY_THRESHOLDS
- **Source**: `app_config.py` → `ANALYSIS_RESILIENCE_LEVEL_SCORES` (derived)
- **Used by**: Analysis for recovery level categorization
- **Values**: `{"low": 50, "moderate": 70}`

### ✅ WHOOP_SPORT_MAPPINGS
- **Source**: `app_config.py` → `WHOOP_SPORT_NAMES`
- **Used by**: Whoop processor for sport ID → name mapping
- **Values**: `{18: "Rowing", 63: "Walking", 65: "Elliptical", 66: "Stairmaster", 45: "Weightlifting", 123: "Strength"}`

### ✅ WITHINGS_MEASUREMENT_TYPES
- **Source**: `app_config.py` → `WITHINGS_MEASUREMENT_TYPE_*` constants
- **Used by**: Withings processor for measurement type mapping
- **Values**: `{1: "weight", 4: "height", 5: "fat_free_mass", ...}`

## ❌ Removed Speculative Features

### MACRO_TARGETS
- **Status**: REMOVED - Not used in current codebase
- **Reason**: No macro ratio analysis exists yet

### HR_ZONES  
- **Status**: REMOVED - Not used in current codebase
- **Reason**: No heart rate zone analysis exists yet

### OURA_ACTIVITY_MAPPINGS
- **Status**: REMOVED - Not used in current codebase  
- **Reason**: Current Oura processor doesn't use activity classifications

## Guidelines for Adding New Configuration

### ✅ DO Add Configuration When:
1. **Code already exists** that uses the values
2. **Immediate need** in current refactoring phase
3. **Direct replacement** of existing hardcoded values

### ❌ DON'T Add Configuration For:
1. **Future features** that don't exist yet
2. **Speculative use cases** without concrete implementation
3. **"Nice to have"** features without current usage

## Process for Adding New Config

1. **Identify existing usage** in current codebase
2. **Extract hardcoded values** to configuration
3. **Update this tracking document** with source and usage
4. **Add to YAML example** with comments about current usage
5. **Test that configuration is actually used**

## Migration from app_config.py

### Completed ✅
- [x] `ANALYSIS_STRENGTH_ACTIVITIES` → `STRENGTH_ACTIVITIES`
- [x] `REPORTING_CALORIC_TARGETS` → `CALORIC_TARGETS`  
- [x] `WHOOP_SPORT_NAMES` → `WHOOP_SPORT_MAPPINGS`
- [x] `WITHINGS_MEASUREMENT_TYPE_*` → `WITHINGS_MEASUREMENT_TYPES`

### Remaining (for future phases)
- [ ] `REPORTING_COLORS` - When updating reporting module
- [ ] `REPORTING_THRESHOLDS` - When updating reporting module
- [ ] `REPORTING_STYLING` - When updating reporting module
- [ ] `REPORTING_CALORIE_FACTORS` - When updating nutrition analysis

## Enum Cleanup (Applied Same Principle)

### ✅ SportType - Minimal Set
- **Kept**: `ROWING`, `WALKING`, `STRENGTH_TRAINING`, `OTHER`, `UNKNOWN`
- **Removed**: `CYCLING`, `RUNNING`, `YOGA`, `SWIMMING`, `BASKETBALL`, `SOCCER`, `TENNIS`, `GOLF`, `HIKING`, `BOXING`, `MARTIAL_ARTS`, `DANCE`, `CLIMBING`, `SKIING`, `SNOWBOARDING`, `SURFING`
- **Reason**: Only kept sports that appear in current `WHOOP_SPORT_MAPPINGS` + required `UNKNOWN`

### ✅ Other Enums - Kept Minimal
- **DataSource**: All 5 values used (whoop, oura, withings, hevy, nutrition_file)
- **WorkoutIntensity**: Kept all 4 values (used in WorkoutRecord model)
- **RecoveryLevel**: Kept all 3 values (used by recovery threshold logic)
- **SleepStage**: Kept all 4 values (used in SleepRecord model)

## Validation Commands

```bash
# Test that config loads without errors
python -c "from src.config import default_config; print('✅ Config loads')"

# Test that all exported constants exist
python -c "from src.config import STRENGTH_ACTIVITIES, CALORIC_TARGETS, RECOVERY_THRESHOLDS, WHOOP_SPORT_MAPPINGS, WITHINGS_MEASUREMENT_TYPES; print('✅ All constants exist')"

# Test that config methods work
python -c "from src.config import default_config; print(f'Sport 45: {default_config.get_whoop_sport_name(45)}'); print(f'Calories: {default_config.get_caloric_target(True)}')"

# Test that enums load without errors
python -c "from src.models import DataSource, SportType, WorkoutIntensity, RecoveryLevel, SleepStage; print('✅ All enums load')"

# Test available sport types
python -c "from src.models import SportType; print(f'Available sports: {[s.value for s in SportType]}')"
```

## Review Checklist

Before adding new configuration:
- [ ] Does code currently exist that uses this?
- [ ] Is this replacing hardcoded values?
- [ ] Is this needed for current phase of refactoring?
- [ ] Have I updated this tracking document?
- [ ] Have I tested that the config is actually used?

This prevents configuration bloat and keeps the codebase focused on actual needs rather than speculative features.

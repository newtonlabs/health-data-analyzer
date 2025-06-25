# Configuration System Architecture

## Overview

The configuration system provides user-customizable settings that are used across **all stages** of the health data pipeline. This allows users to personalize their experience without modifying code.

## Directory Structure

```
src/
├── config/
│   ├── __init__.py           # Configuration module exports
│   └── user_config.py        # UserConfig class and defaults
├── models/                   # Data models (imports config)
├── api/services/            # API services (uses config)
├── processing/
│   ├── extractors/          # Data extractors (uses config)
│   ├── transformers/        # Data transformers (uses config)
│   └── aggregators/         # Data aggregators (uses config)
└── reporting/               # Report generation (uses config)

config/
└── user_config.yaml.example # Example user configuration
```

## Configuration Usage Across Pipeline Stages

### 1. **API Services** - Data Fetching
```python
from src.config import default_config

class WhoopService:
    def __init__(self):
        self.config = default_config
    
    def fetch_workouts(self, raw_data):
        # No configuration needed - just fetch raw data
        return self.client.get_workouts()
```

### 2. **Extractors** - Raw Data → Structured Records
```python
from src.config import default_config
from src.models import WorkoutRecord, DataSource, SportType

class WhoopExtractor:
    def __init__(self, config: UserConfig = None):
        self.config = config or default_config
    
    def extract_workouts(self, raw_data):
        workouts = []
        for workout in raw_data.get('data', []):
            # Use config for API ID mapping
            sport_info = self.config.get_whoop_sport_info(workout['sport_id'])
            
            workout_record = WorkoutRecord(
                source=DataSource.WHOOP,
                sport=SportType(sport_info['sport_type']),
                # ... other fields
            )
            workouts.append(workout_record)
        return workouts
```

### 3. **Transformers** - Data Cleaning & Normalization
```python
from src.config import default_config

class CalorieTransformer:
    def __init__(self, config: UserConfig = None):
        self.config = config or default_config
    
    def transform_nutrition(self, nutrition_records):
        for record in nutrition_records:
            # Use config to determine if it's a strength day
            record.is_strength_day = self.config.is_strength_activity(
                record.associated_workout_sport
            )
            
            # Get target calories based on day type
            record.target_calories = self.config.get_caloric_target(
                record.is_strength_day
            )
        return nutrition_records
```

### 4. **Aggregators** - Analysis & Metrics
```python
from src.config import default_config

class RecoveryAggregator:
    def __init__(self, config: UserConfig = None):
        self.config = config or default_config
    
    def analyze_recovery_trends(self, recovery_records):
        metrics = {}
        for record in recovery_records:
            # Use config thresholds for categorization
            level = self.config.get_recovery_level(record.recovery_score)
            
            # Aggregate based on user's thresholds
            if level not in metrics:
                metrics[level] = []
            metrics[level].append(record)
        
        return metrics
```

### 5. **Reporting** - Visualization & Output
```python
from src.config import default_config

class NutritionReporter:
    def __init__(self, config: UserConfig = None):
        self.config = config or default_config
    
    def generate_macro_chart(self, nutrition_data):
        # Use config for macro targets
        for day_type in ['strength_day', 'rest_day']:
            targets = self.config.macro_targets[day_type]
            
            # Create charts with user's target lines
            self.add_target_line(targets['protein_pct'], 'Protein Target')
            self.add_target_line(targets['carbs_pct'], 'Carbs Target')
            self.add_target_line(targets['fat_pct'], 'Fat Target')
```

## Configuration Categories

### 1. **Activity Classifications**
- `strength_activities`: Which sports count as strength training
- Used by: Extractors, Transformers, Aggregators

### 2. **Caloric Targets**
- `caloric_targets`: Daily calorie goals by activity type
- Used by: Transformers, Aggregators, Reporting

### 3. **Recovery Thresholds**
- `recovery_thresholds`: Score ranges for low/moderate/high recovery
- Used by: Extractors, Aggregators, Reporting

### 4. **API ID Mappings**
- `whoop_sport_mappings`: Whoop sport ID → name + type
- `oura_activity_mappings`: Oura activity class → name + type
- `withings_measurement_types`: Withings measurement type IDs
- Used by: Extractors

### 5. **Macro Targets**
- `macro_targets`: Protein/carbs/fat percentages by day type
- Used by: Transformers, Aggregators, Reporting

### 6. **Heart Rate Zones**
- `hr_zones`: HR thresholds for intensity classification
- Used by: Extractors, Transformers, Aggregators

## Usage Patterns

### Default Configuration
```python
from src.config import default_config

# Use default settings
sport_name = default_config.get_whoop_sport_name(45)  # "Weightlifting"
target_cals = default_config.get_caloric_target(True)  # 2400
```

### Custom Configuration
```python
from src.config import UserConfig

# Create custom config
custom_config = UserConfig.from_dict({
    "caloric_targets": {"strength_day": 2600, "rest_day": 1800},
    "recovery_thresholds": {"low": 40, "moderate": 65}
})

# Use custom settings
target_cals = custom_config.get_caloric_target(True)  # 2600
```

### YAML Configuration (Future)
```python
from src.config import UserConfig

# Load from YAML file
user_config = UserConfig.from_yaml('config/user_config.yaml')

# Use throughout pipeline
pipeline = HealthDataPipeline(config=user_config)
```

## Benefits

### 1. **Personalization**
- Users can customize targets, thresholds, and classifications
- No code changes required for personalization

### 2. **Consistency**
- Same configuration used across all pipeline stages
- Single source of truth for user preferences

### 3. **Extensibility**
- Easy to add new configurable parameters
- YAML support for non-technical users

### 4. **Testability**
- Different configurations for testing scenarios
- Easy to mock configuration in tests

### 5. **Maintainability**
- Configuration separate from business logic
- Clear separation of concerns

## Migration Path

### Phase 1: ✅ Foundation
- Created `src/config/` module
- Moved configurable constants from `models/enums.py`
- Added `UserConfig` class with helper methods

### Phase 2: Integration (Next)
- Update extractors to use config for API mappings
- Update transformers to use config for thresholds
- Update aggregators to use config for categorization

### Phase 3: YAML Support
- Implement `UserConfig.from_yaml()`
- Add YAML parsing and validation
- Create user-friendly configuration interface

### Phase 4: Advanced Features
- Environment variable overrides
- Configuration validation and error handling
- Dynamic configuration reloading

## Example User Workflow

1. **Copy example config**: `cp config/user_config.yaml.example config/user_config.yaml`
2. **Customize settings**: Edit caloric targets, recovery thresholds, etc.
3. **Run pipeline**: `python main.py --config config/user_config.yaml`
4. **Get personalized results**: Reports use your custom settings

This architecture ensures that user preferences are respected throughout the entire data processing pipeline while maintaining clean separation of concerns.

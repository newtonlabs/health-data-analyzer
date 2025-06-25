# Health Data Pipeline Architecture Guidelines

## Overview

This document defines the clean 5-stage pipeline architecture for health data processing, with clear separation of concerns and responsibilities at each stage.

## Pipeline Architecture

```
Stage 1: API Service    → Raw JSON response
Stage 2: Extractor      → Raw data models  
Stage 3: Transformer    → Clean data models
Stage 4: Aggregator     → Summary models (future)
Stage 5: Reporter       → Visualizations (future)
```

## Stage Responsibilities

### Stage 1: API Service
**Purpose**: Pure API communication and authentication

**Responsibilities:**
- Handle API authentication (OAuth2, API keys)
- Make HTTP requests to external APIs
- Return raw JSON responses
- Handle rate limiting and retries
- NO data processing or transformation

**Examples:**
- `WhoopService.get_workouts()` → Raw JSON from Whoop API
- `HevyService.get_workouts_data()` → Raw JSON from Hevy API

**File Location:** `src/api/services/`

---

### Stage 2: Extractor
**Purpose**: Convert raw API JSON to basic data models

**Responsibilities:**
- Parse API response structure
- Map API fields to model fields
- Basic data type conversion (string → datetime, etc.)
- Create raw data models with minimal processing
- Preserve original data structure and values
- **NO data cleaning, validation, or transformation**

**What to do:**
- Convert JSON arrays to lists of model objects
- Parse ISO timestamps to datetime objects
- Map API field names to model field names
- Handle missing/null values gracefully

**What NOT to do:**
- Round numbers or modify precision
- Validate data ranges or reasonableness
- Clean or normalize text fields
- Filter out records
- Convert timezones

**Examples:**
```python
# ✅ Good - Pure extraction
record = WorkoutRecord(
    timestamp=datetime.fromisoformat(workout["start_time"]),
    weight_kg=set_data.get("weight_kg"),  # Keep original precision
    exercise_name=exercise.get("title")   # Keep original text
)

# ❌ Bad - This belongs in Transformer
record = WorkoutRecord(
    weight_kg=round(set_data.get("weight_kg"), 2),  # Don't round here
    exercise_name=exercise.get("title", "").strip().title()  # Don't clean here
)
```

**File Location:** `src/processing/extractors/`

---

### Stage 3: Transformer
**Purpose**: Clean, validate, and normalize extracted data

**Responsibilities:**
- **Rounding**: Round weights to 2 decimals, durations to integers
- **Timezone conversion**: Convert timestamps to consistent timezone
- **Data validation**: Check for reasonable ranges, required fields
- **Normalization**: Standardize units, formats, naming conventions
- **Filtering**: Remove invalid or outlier records
- **Field standardization**: Clean exercise names, normalize text
- **Unit conversion**: Ensure consistent units (kg, meters, etc.)

**What to do:**
- Round numerical values to appropriate precision
- Convert all timestamps to consistent timezone (UTC recommended)
- Validate data ranges (RPE 1-10, reasonable weights, etc.)
- Standardize text formatting (title case, trim whitespace)
- Filter out invalid records
- Normalize units across different APIs

**What NOT to do:**
- Calculate derived metrics or summaries
- Combine data from multiple records
- Create new aggregated models
- Cross-reference data from other services

**Examples:**
```python
# ✅ Good - Data cleaning and normalization
def _normalize_weight(self, weight: Optional[float]) -> Optional[float]:
    if weight is None:
        return None
    return round(weight, 2)  # 92.532954 → 92.53

def _normalize_exercise_name(self, name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    return name.strip().title()  # "t bar row" → "T Bar Row"

def validate_record(self, record: ExerciseRecord) -> bool:
    # Validate RPE is in reasonable range
    if record.rpe and (record.rpe < 1 or record.rpe > 10):
        return False
    return True
```

**File Location:** `src/processing/transformers/`

---

### Stage 4: Aggregator (Future Implementation)
**Purpose**: Analyze and summarize transformed data

**Responsibilities:**
- **Rollup calculations**: Weekly/monthly summaries
- **Cross-service analysis**: Combine data from multiple services
- **Derived metrics**: Calculate training load, recovery ratios, trends
- **New model creation**: WeeklySummaryRecord, ProgressRecord
- **Trend analysis**: Moving averages, progression tracking
- **Data relationships**: Link related records across services

**What to do:**
- Create summary models from multiple records
- Calculate derived metrics and trends
- Combine data from different services for analysis
- Generate time-based rollups (daily, weekly, monthly)
- Identify patterns and correlations

**Examples:**
```python
# ✅ Future - Data aggregation and analysis
class WeeklyStrengthSummary:
    week_start: date
    total_volume_kg: float
    total_sets: int
    exercises_performed: List[str]
    avg_rpe: float
    progression_vs_last_week: float

def create_weekly_summary(exercise_records: List[ExerciseRecord]) -> WeeklyStrengthSummary:
    # Aggregate individual exercise records into weekly summary
    pass

def calculate_training_load(whoop_strain: float, hevy_volume: float) -> float:
    # Combine Whoop and Hevy data for comprehensive training load
    pass
```

**File Location:** `src/processing/aggregators/` (future)

---

### Stage 5: Reporter (Future Implementation)
**Purpose**: Present analyzed data for consumption

**Responsibilities:**
- Generate charts, graphs, dashboards
- Export formatted reports (PDF, HTML)
- Create data visualizations
- Prepare data for external tools
- Format data for different output formats

**Examples:**
- Weekly strength progression charts
- Body composition trend graphs
- Training load vs recovery correlation plots
- Formatted PDF workout summaries

**File Location:** `src/reporting/` (future)

---

## Data Flow Examples

### Current Implementation (Stages 1-3)

**Hevy Strength Training Data:**

```
Stage 1 (API Service):
Raw JSON: {"workouts": [{"exercises": [{"sets": [{"weight_kg": 92.532954, "reps": 12}]}]}]}

Stage 2 (Extractor):
ExerciseRecord(weight_kg=92.532954, reps=12, exercise_name="T Bar Row")

Stage 3 (Transformer):
ExerciseRecord(weight_kg=92.53, reps=12, exercise_name="T Bar Row")
```

### Future Implementation (Stages 4-5)

```
Stage 4 (Aggregator):
WeeklyStrengthSummary(total_volume_kg=15509.25, exercises=["T Bar Row", "Dumbbell Row"])

Stage 5 (Reporter):
Chart: "Weekly Back Volume: 15.5 tons" with trend line
```

## Implementation Guidelines

### Adding New Services

1. **Create API Service** (`src/api/services/new_service.py`)
   - Handle authentication
   - Make API calls
   - Return raw JSON

2. **Create Extractor** (`src/processing/extractors/new_extractor.py`)
   - Parse JSON to data models
   - No data cleaning

3. **Create Transformer** (`src/processing/transformers/new_transformer.py`)
   - Clean and normalize data
   - Validate ranges

4. **Update Clean Pipeline** (`src/pipeline/clean_pipeline.py`)
   - Add service, extractor, transformer
   - Create `process_new_service_data()` method

### Data Model Guidelines

- **Keep models focused**: One model per data type (WorkoutRecord, ExerciseRecord, etc.)
- **Use Optional fields**: Most fields should be Optional to handle API variations
- **Include source field**: Always track which service provided the data
- **Consistent naming**: Use clear, descriptive field names
- **Type hints**: Always use proper type hints

### File Organization

```
src/
├── api/services/          # Stage 1: API communication
├── processing/
│   ├── extractors/        # Stage 2: JSON → Models
│   ├── transformers/      # Stage 3: Clean models
│   ├── aggregators/       # Stage 4: Summary models (future)
│   └── base_*.py         # Base classes
├── models/
│   └── data_records.py   # Data model definitions
├── pipeline/
│   └── clean_pipeline.py # Orchestrates all stages
└── reporting/            # Stage 5: Visualizations (future)
```

### Testing Guidelines

- **Test each stage independently**
- **Use real API data for integration tests**
- **Mock API calls for unit tests**
- **Validate data flow through all stages**
- **Test error handling and edge cases**

## Current Status

### ✅ Implemented (Stages 1-3)
- **4 API Services**: Whoop, Oura, Withings, Hevy
- **4 Extractors**: Pure data extraction
- **5 Transformers**: Data cleaning (including ExerciseTransformer)
- **Complete pipeline**: All services use clean 3-stage architecture
- **Rich data extraction**: Workout summaries + individual exercise details

### 🚧 Future Work (Stages 4-5)
- **Aggregator stage**: Weekly/monthly summaries, cross-service analysis
- **Reporter stage**: Charts, dashboards, formatted reports
- **Advanced analytics**: Trend analysis, correlation detection
- **Data export**: Integration with external tools

## Key Principles

1. **Single Responsibility**: Each stage has one clear purpose
2. **Clean Separation**: No mixing of concerns between stages
3. **Data Lineage**: Complete traceability from API to final output
4. **Observability**: Data saved at each stage for debugging
5. **Extensibility**: Easy to add new services following same pattern
6. **Maintainability**: Clear structure makes code easy to understand and modify

---

*This document should be updated as the pipeline evolves and new stages are implemented.*

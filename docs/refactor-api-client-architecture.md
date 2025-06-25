# API Client Architecture Refactor Recommendation

## Executive Summary

This document outlines a comprehensive refactoring plan for the health-data-analyzer API client architecture to improve code consistency, maintainability, and adherence to SOLID principles. The refactor separates concerns across data fetching, processing, aggregation, and reporting stages.

## Current Architecture Issues

### 1. Inconsistent Inheritance Patterns
- **WhoopClient**, **WithingsClient**, **OneDriveClient**, and **HevyClient** properly extend `APIClient`
- **OuraClient** does NOT extend `APIClient` - it's a standalone implementation that duplicates functionality
- This breaks the Liskov Substitution Principle and creates maintenance overhead

### 2. Duplicated Code Patterns
- Each client reimplements `_make_request` with similar but slightly different logic
- Token management code is duplicated across clients
- Authentication flows are similar but inconsistent
- Error handling patterns vary between clients

### 3. Single Responsibility Violations
- Clients handle both API communication AND data transformation
- Authentication logic mixed with business logic
- Token management scattered across multiple classes

### 4. Inconsistent Method Signatures
- `_make_request` methods have different parameters across clients
- Some use `APIClientError`, others use custom exceptions (`OuraError`)
- Different approaches to retry logic and error handling

### 5. Mixed Data Flow Responsibilities
- API clients handle both data fetching AND some processing logic
- Tight coupling between workflow and API client methods
- Inconsistent processing with some normalization in clients, some in processors
- No clear separation between raw data, processed data, and aggregated data

## Recommended Architecture

### New Directory Structure

```
src/
├── api/                    # Pure API communication layer
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base_service.py
│   │   ├── whoop_service.py
│   │   ├── oura_service.py
│   │   ├── withings_service.py
│   │   └── hevy_service.py
│   └── __init__.py
├── clients/                # Authentication and connection management
│   ├── __init__.py
│   ├── base_client.py
│   ├── whoop_client.py
│   ├── oura_client.py
│   ├── withings_client.py
│   ├── hevy_client.py
│   └── onedrive_client.py
├── models/                 # Data models and type definitions
│   ├── __init__.py
│   ├── data_records.py
│   ├── collections.py
│   └── enums.py
├── processing/             # Data transformation pipeline
│   ├── __init__.py
│   ├── extractors/         # Raw API response → structured data
│   │   ├── __init__.py
│   │   ├── base_extractor.py
│   │   ├── whoop_extractor.py
│   │   ├── oura_extractor.py
│   │   ├── withings_extractor.py
│   │   └── hevy_extractor.py
│   ├── transformers/       # Normalization, timezone, cleaning
│   │   ├── __init__.py
│   │   ├── base_transformer.py
│   │   ├── timezone_transformer.py
│   │   ├── data_cleaner.py
│   │   └── data_validator.py
│   ├── aggregators/        # Analysis and calculations
│   │   ├── __init__.py
│   │   ├── base_aggregator.py
│   │   ├── recovery_aggregator.py
│   │   ├── training_aggregator.py
│   │   └── macros_aggregator.py
│   └── pipeline.py         # Main pipeline orchestration
└── reporting/              # Visualization and output (existing)
```

### Data Flow Architecture

```python
# Stage 1: Raw Data Extraction
class DataExtractor:
    """Extracts raw data from API services"""
    def extract_all_sources(self, start_date, end_date) -> RawDataCollection
    
# Stage 2: Data Transformation  
class DataTransformer:
    """Normalizes and cleans raw data"""
    def transform(self, raw_data: RawDataCollection) -> ProcessedDataCollection
    
# Stage 3: Data Aggregation
class DataAggregator:
    """Performs analysis and calculations"""
    def aggregate(self, processed_data: ProcessedDataCollection) -> AggregatedMetrics
    
# Stage 4: Report Generation
class ReportGenerator:
    """Creates visualizations and reports"""
    def generate(self, metrics: AggregatedMetrics) -> Report
```

## Implementation Details

### 1. API Services Layer (Pure Data Fetching)

```python
# src/api/services/base_service.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

class BaseAPIService(ABC):
    """Base class for all API services"""
    
    def __init__(self, client):
        self.client = client
    
    @abstractmethod
    def fetch_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch raw data from API - no processing"""
        pass

# src/api/services/whoop_service.py
class WhoopService(BaseAPIService):
    """Pure API service for Whoop data fetching"""
    
    def fetch_workouts(self, start_date: datetime, end_date: datetime) -> dict:
        """Fetch raw workout data - no processing"""
        return self.client._make_request("v1/activity/workout", {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        })
    
    def fetch_recovery(self, start_date: datetime, end_date: datetime) -> dict:
        """Fetch raw recovery data - no processing"""
        return self.client._make_request("v1/recovery", {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        })
    
    def fetch_sleep(self, start_date: datetime, end_date: datetime) -> dict:
        """Fetch raw sleep data - no processing"""
        return self.client._make_request("v1/activity/sleep", {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        })
```

### 2. Data Models for Type Safety

```python
# src/models/data_records.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class WorkoutRecord:
    timestamp: datetime
    source: str  # 'whoop', 'hevy', etc.
    sport: str
    duration_minutes: int
    strain_score: Optional[float] = None
    calories: Optional[int] = None
    
@dataclass
class RecoveryRecord:
    date: datetime
    source: str
    recovery_score: Optional[int] = None
    hrv_rmssd: Optional[float] = None
    resting_hr: Optional[int] = None

@dataclass
class WeightRecord:
    timestamp: datetime
    source: str
    weight_kg: float
    
@dataclass
class NutritionRecord:
    date: datetime
    source: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float

# src/models/collections.py
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class RawDataCollection:
    """Raw API responses from all sources"""
    whoop_data: Dict[str, Any]
    oura_data: Dict[str, Any]
    withings_data: Dict[str, Any]
    hevy_data: Dict[str, Any]

@dataclass
class ProcessedDataCollection:
    """Structured and normalized data records"""
    workouts: List[WorkoutRecord]
    recovery: List[RecoveryRecord]
    weight: List[WeightRecord]
    nutrition: List[NutritionRecord]

@dataclass
class AggregatedMetrics:
    """Calculated metrics and analysis results"""
    weekly_stats: Dict[str, Any]
    trends: Dict[str, Any]
    correlations: Dict[str, Any]
```

### 3. Data Extraction Layer

```python
# src/processing/extractors/base_extractor.py
from abc import ABC, abstractmethod
from typing import Any, List
from src.models.data_records import WorkoutRecord, RecoveryRecord

class BaseExtractor(ABC):
    """Base class for data extractors"""
    
    @abstractmethod
    def extract_workouts(self, raw_response: dict) -> List[WorkoutRecord]:
        """Convert raw API response to structured workout records"""
        pass
    
    @abstractmethod
    def extract_recovery(self, raw_response: dict) -> List[RecoveryRecord]:
        """Convert raw API response to structured recovery records"""
        pass

# src/processing/extractors/whoop_extractor.py
class WhoopExtractor(BaseExtractor):
    """Extracts structured data from raw Whoop API responses"""
    
    def extract_workouts(self, raw_response: dict) -> List[WorkoutRecord]:
        """Convert raw Whoop workout response to structured records"""
        workouts = []
        for workout in raw_response.get('data', []):
            workouts.append(WorkoutRecord(
                timestamp=self._parse_timestamp(workout['start']),
                source='whoop',
                sport=workout.get('sport_id', 'unknown'),
                duration_minutes=workout.get('score', {}).get('duration_minutes', 0),
                strain_score=workout.get('score', {}).get('strain', None),
                calories=workout.get('score', {}).get('kilojoule', None)
            ))
        return workouts
    
    def extract_recovery(self, raw_response: dict) -> List[RecoveryRecord]:
        """Convert raw Whoop recovery response to structured records"""
        recovery_records = []
        for recovery in raw_response.get('data', []):
            recovery_records.append(RecoveryRecord(
                date=self._parse_date(recovery['cycle_id']),
                source='whoop',
                recovery_score=recovery.get('score', {}).get('recovery_score'),
                hrv_rmssd=recovery.get('score', {}).get('hrv_rmssd_milli'),
                resting_hr=recovery.get('score', {}).get('resting_heart_rate')
            ))
        return recovery_records
```

### 4. Data Transformation Layer

```python
# src/processing/transformers/timezone_transformer.py
from typing import List
from src.models.data_records import WorkoutRecord, RecoveryRecord
from src.utils.date_utils import DateUtils

class TimezoneTransformer:
    """Handles timezone normalization across all data sources"""
    
    def normalize_workout_timestamps(self, workouts: List[WorkoutRecord]) -> List[WorkoutRecord]:
        """Convert all workout timestamps to consistent timezone"""
        for workout in workouts:
            workout.timestamp = DateUtils.to_local_timezone(workout.timestamp)
        return workouts
    
    def normalize_recovery_dates(self, recovery: List[RecoveryRecord]) -> List[RecoveryRecord]:
        """Convert all recovery dates to consistent timezone"""
        for record in recovery:
            record.date = DateUtils.to_local_timezone(record.date)
        return recovery

# src/processing/transformers/data_cleaner.py
class DataCleaner:
    """Handles data cleaning and validation"""
    
    def clean_workouts(self, workouts: List[WorkoutRecord]) -> List[WorkoutRecord]:
        """Clean and validate workout records"""
        cleaned = []
        for workout in workouts:
            if self._is_valid_workout(workout):
                cleaned.append(self._clean_workout(workout))
        return cleaned
    
    def _is_valid_workout(self, workout: WorkoutRecord) -> bool:
        """Validate workout record"""
        return (
            workout.timestamp is not None and
            workout.duration_minutes > 0 and
            workout.sport is not None
        )
    
    def _clean_workout(self, workout: WorkoutRecord) -> WorkoutRecord:
        """Clean individual workout record"""
        # Normalize sport names
        workout.sport = self._normalize_sport_name(workout.sport)
        
        # Cap unrealistic values
        if workout.duration_minutes > 600:  # 10 hours max
            workout.duration_minutes = 600
            
        return workout
```

### 5. Pipeline Orchestration

```python
# src/processing/pipeline.py
from datetime import datetime
from typing import Dict, Any

from src.api.services.whoop_service import WhoopService
from src.api.services.oura_service import OuraService
from src.api.services.withings_service import WithingsService
from src.api.services.hevy_service import HevyService

from src.processing.extractors.whoop_extractor import WhoopExtractor
from src.processing.extractors.oura_extractor import OuraExtractor
from src.processing.extractors.withings_extractor import WithingsExtractor
from src.processing.extractors.hevy_extractor import HevyExtractor

from src.processing.transformers.timezone_transformer import TimezoneTransformer
from src.processing.transformers.data_cleaner import DataCleaner

from src.models.collections import RawDataCollection, ProcessedDataCollection

class HealthDataPipeline:
    """Orchestrates the entire data processing pipeline"""
    
    def __init__(self):
        # Initialize API services
        self.whoop_service = WhoopService(WhoopClient())
        self.oura_service = OuraService(OuraClient())
        self.withings_service = WithingsService(WithingsClient())
        self.hevy_service = HevyService(HevyClient())
        
        # Initialize extractors
        self.whoop_extractor = WhoopExtractor()
        self.oura_extractor = OuraExtractor()
        self.withings_extractor = WithingsExtractor()
        self.hevy_extractor = HevyExtractor()
        
        # Initialize transformers
        self.timezone_transformer = TimezoneTransformer()
        self.data_cleaner = DataCleaner()
    
    def run_pipeline(self, start_date: datetime, end_date: datetime) -> ProcessedDataCollection:
        """Run the complete data processing pipeline"""
        
        # Stage 1: Fetch raw data from all sources
        raw_data = self._fetch_all_raw_data(start_date, end_date)
        
        # Stage 2: Extract structured data from raw responses
        extracted_data = self._extract_structured_data(raw_data)
        
        # Stage 3: Transform and normalize data
        processed_data = self._transform_and_normalize(extracted_data)
        
        return processed_data
    
    def _fetch_all_raw_data(self, start_date: datetime, end_date: datetime) -> RawDataCollection:
        """Fetch raw data from all API sources"""
        return RawDataCollection(
            whoop_data={
                'workouts': self.whoop_service.fetch_workouts(start_date, end_date),
                'recovery': self.whoop_service.fetch_recovery(start_date, end_date),
                'sleep': self.whoop_service.fetch_sleep(start_date, end_date)
            },
            oura_data={
                'activity': self.oura_service.fetch_activity(start_date, end_date),
                'resilience': self.oura_service.fetch_resilience(start_date, end_date)
            },
            withings_data={
                'weight': self.withings_service.fetch_weight(start_date, end_date)
            },
            hevy_data=self.hevy_service.fetch_workouts()
        )
    
    def _extract_structured_data(self, raw_data: RawDataCollection) -> ProcessedDataCollection:
        """Extract structured data from raw API responses"""
        all_workouts = []
        all_recovery = []
        all_weight = []
        
        # Extract Whoop data
        all_workouts.extend(self.whoop_extractor.extract_workouts(raw_data.whoop_data['workouts']))
        all_recovery.extend(self.whoop_extractor.extract_recovery(raw_data.whoop_data['recovery']))
        
        # Extract Oura data
        all_recovery.extend(self.oura_extractor.extract_recovery(raw_data.oura_data['resilience']))
        
        # Extract Withings data
        all_weight.extend(self.withings_extractor.extract_weight(raw_data.withings_data['weight']))
        
        # Extract Hevy data
        all_workouts.extend(self.hevy_extractor.extract_workouts(raw_data.hevy_data))
        
        return ProcessedDataCollection(
            workouts=all_workouts,
            recovery=all_recovery,
            weight=all_weight,
            nutrition=[]  # Load from file source
        )
    
    def _transform_and_normalize(self, data: ProcessedDataCollection) -> ProcessedDataCollection:
        """Transform and normalize the extracted data"""
        
        # Normalize timezones
        data.workouts = self.timezone_transformer.normalize_workout_timestamps(data.workouts)
        data.recovery = self.timezone_transformer.normalize_recovery_dates(data.recovery)
        
        # Clean and validate data
        data.workouts = self.data_cleaner.clean_workouts(data.workouts)
        data.recovery = self.data_cleaner.clean_recovery(data.recovery)
        data.weight = self.data_cleaner.clean_weight(data.weight)
        
        return data
```

## Migration Strategy

### Phase 1: Foundation (Week 1)
1. **Create new directory structure**
   - Set up `src/api/`, `src/models/`, `src/processing/` directories
   - Create `__init__.py` files for proper Python packages

2. **Define data models**
   - Implement `data_records.py` with all record types
   - Create `collections.py` for pipeline data containers
   - Add `enums.py` for constants and enumerations

3. **Create base classes**
   - Implement `BaseAPIService`, `BaseExtractor`, `BaseTransformer`
   - Establish common interfaces and patterns

### Phase 2: Extract API Services (Week 2)
1. **Start with Whoop (establish pattern)**
   - Create `WhoopService` for pure API calls
   - Refactor `WhoopClient` to focus on authentication only
   - Create `WhoopExtractor` for data extraction

2. **Apply pattern to other services**
   - Implement `OuraService`, `WithingsService`, `HevyService`
   - Standardize `OuraClient` to extend `APIClient`
   - Create corresponding extractors

### Phase 3: Build Processing Pipeline (Week 3)
1. **Implement transformers**
   - Create `TimezoneTransformer` for consistent timezone handling
   - Implement `DataCleaner` for validation and cleaning
   - Add `DataValidator` for data quality checks

2. **Build main pipeline**
   - Implement `HealthDataPipeline` orchestration
   - Create pipeline stages with clear interfaces
   - Add comprehensive logging and error handling

### Phase 4: Update Aggregators and Reporting (Week 4)
1. **Refactor aggregators**
   - Update aggregators to work with new data models
   - Ensure consistent data access patterns
   - Maintain existing functionality

2. **Update workflow integration**
   - Refactor main workflow to use new pipeline
   - Update CLI interface if needed
   - Ensure backward compatibility

### Phase 5: Testing and Validation (Week 5)
1. **Comprehensive testing**
   - Unit tests for all new components
   - Integration tests for pipeline stages
   - End-to-end testing with real data

2. **Performance validation**
   - Ensure no performance regression
   - Optimize pipeline stages if needed
   - Validate memory usage patterns

## Benefits of New Architecture

### 1. Single Responsibility Principle
- **API Services**: Only handle API communication
- **Extractors**: Only convert raw responses to structured data
- **Transformers**: Only handle normalization and cleaning
- **Aggregators**: Only perform analysis and calculations

### 2. DRY (Don't Repeat Yourself)
- Common authentication logic centralized in base client
- Shared data transformation logic in transformer classes
- Consistent error handling across all services
- Reusable data models across the entire pipeline

### 3. Open/Closed Principle
- Easy to add new data sources without modifying existing code
- New transformation steps can be added to the pipeline
- Extensible aggregation and reporting capabilities

### 4. Dependency Inversion
- High-level pipeline doesn't depend on specific API implementations
- Interfaces define contracts between components
- Easy to mock and test individual components

### 5. Improved Testability
- Each component can be tested in isolation
- Clear data contracts make mocking straightforward
- Pipeline stages can be tested independently

### 6. Enhanced Maintainability
- Changes to one component don't affect others
- Clear separation of concerns makes debugging easier
- Consistent patterns across all data sources

## Conclusion

This refactoring will significantly improve the codebase's maintainability, testability, and extensibility while adhering to SOLID principles. The clear separation of concerns and consistent patterns will make it easier to add new data sources and modify existing functionality without introducing bugs or breaking changes.

The migration can be done incrementally, allowing for continuous validation and testing throughout the process. The new architecture provides a solid foundation for future enhancements and scaling of the health data analysis system.

"""Training aggregator for combining workout and training load data."""

from datetime import date
from typing import List, Optional

from src.models.raw_data import WorkoutRecord
from src.models.aggregations import TrainingMetricsRecord
from src.models.enums import SportType


class TrainingAggregator:
    """Aggregator for combining workout data into daily training summaries."""
    
    def aggregate_daily_training(
        self,
        target_date: date,
        workout_records: List[WorkoutRecord]
    ) -> TrainingMetricsRecord:
        """Aggregate daily workout data into training metrics.
        
        Args:
            target_date: Date to aggregate data for
            workout_records: Workout data for the date
            
        Returns:
            Aggregated daily training metrics record
        """
        # Find workouts for target date
        daily_workouts = self._find_workouts_for_date(workout_records, target_date)
        
        if not daily_workouts:
            return TrainingMetricsRecord(
                date=target_date,
                day=target_date.strftime("%a"),
                sport=None,
                duration=None,
                strain=None,
                workout_count=0,
                calories_burned=None,
            )
        
        # Calculate aggregated metrics
        total_duration = sum(w.duration_minutes for w in daily_workouts)
        total_calories = sum(w.calories for w in daily_workouts if w.calories)
        avg_strain = sum(w.strain_score for w in daily_workouts if w.strain_score) / len([w for w in daily_workouts if w.strain_score]) if any(w.strain_score for w in daily_workouts) else None
        
        # Determine primary sport (most time spent)
        primary_sport = self._determine_primary_sport(daily_workouts)
        
        return TrainingMetricsRecord(
            date=target_date,
            day=target_date.strftime("%a"),
            sport=primary_sport,
            duration=total_duration,
            strain=avg_strain,
            workout_count=len(daily_workouts),
            calories_burned=total_calories if total_calories > 0 else None,
        )
    
    def _find_workouts_for_date(self, records: List[WorkoutRecord], target_date: date) -> List[WorkoutRecord]:
        """Find all workout records for specific date."""
        return [record for record in records if record.date == target_date]
    
    def _determine_primary_sport(self, workouts: List[WorkoutRecord]) -> Optional[SportType]:
        """Determine primary sport based on total duration per sport."""
        if not workouts:
            return None
        
        # Group by sport and sum durations
        sport_durations = {}
        for workout in workouts:
            sport = workout.sport
            if sport not in sport_durations:
                sport_durations[sport] = 0
            sport_durations[sport] += workout.duration_minutes
        
        # Return sport with most total duration
        return max(sport_durations.items(), key=lambda x: x[1])[0]
    
    # Business logic methods (moved from model)
    @staticmethod
    def categorize_training_intensity(strain: float) -> str:
        """Categorize training intensity based on strain score."""
        if strain >= 15:
            return "very_high"
        elif strain >= 12:
            return "high"
        elif strain >= 8:
            return "moderate"
        elif strain >= 4:
            return "low"
        else:
            return "very_low"
    
    @staticmethod
    def categorize_duration(duration: int) -> str:
        """Categorize workout duration."""
        if duration >= 90:
            return "long"
        elif duration >= 45:
            return "medium"
        elif duration >= 20:
            return "short"
        else:
            return "very_short"
    
    @staticmethod
    def calculate_strain_per_minute(strain: float, duration: int) -> float:
        """Calculate strain efficiency (strain per minute of training)."""
        if duration == 0:
            return 0.0
        return round(strain / duration, 3)
    
    @staticmethod
    def calculate_training_load_score(strain: float, duration: int) -> float:
        """Calculate a composite training load score (0-100)."""
        # Combine strain and duration into a load score
        # Higher strain and longer duration = higher load
        strain_component = min(100, (strain / 20) * 100)  # Normalize to 100
        duration_component = min(100, (duration / 120) * 100)  # 2 hours = 100
        
        # Weighted combination (strain is more important than duration)
        load_score = (strain_component * 0.7) + (duration_component * 0.3)
        return round(load_score, 1)
    
    @staticmethod
    def is_rest_day(duration: Optional[int], strain: Optional[float]) -> bool:
        """Determine if this is a rest day (no significant training)."""
        return (not duration or duration < 15) and (not strain or strain < 2)
    
    @staticmethod
    def categorize_sport(sport: SportType) -> str:
        """Group sports into broader categories for analysis."""
        strength_sports = [SportType.STRENGTH_TRAINING]
        cardio_sports = [SportType.WALKING, SportType.ROWING]
        
        if sport in strength_sports:
            return "strength"
        elif sport in cardio_sports:
            return "cardio"
        else:
            return "other"
    
    @staticmethod
    def generate_training_summary(record: TrainingMetricsRecord) -> dict:
        """Generate a summary dictionary for easy reporting."""
        return {
            "date": record.date.isoformat(),
            "day": record.day,
            "sport": record.sport.value if record.sport else None,
            "sport_category": TrainingAggregator.categorize_sport(record.sport) if record.sport else None,
            "duration_min": record.duration,
            "duration_category": TrainingAggregator.categorize_duration(record.duration) if record.duration else None,
            "strain": record.strain,
            "intensity": TrainingAggregator.categorize_training_intensity(record.strain) if record.strain else None,
            "load_score": TrainingAggregator.calculate_training_load_score(record.strain, record.duration) if record.strain and record.duration else None,
            "strain_efficiency": TrainingAggregator.calculate_strain_per_minute(record.strain, record.duration) if record.strain and record.duration else None,
            "is_rest_day": TrainingAggregator.is_rest_day(record.duration, record.strain),
            "workout_count": record.workout_count,
            "calories": record.calories_burned,
        }

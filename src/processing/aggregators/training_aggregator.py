"""Training aggregator for combining workout and training load data."""

from datetime import date
from typing import List

from src.models.raw_data import WorkoutRecord
from src.models.aggregations import TrainingMetricsRecord


class TrainingAggregator:
    """Aggregator for combining workout data into daily training summaries."""
    
    def aggregate_daily_training(
        self,
        target_date: date,
        workout_records: List[WorkoutRecord]
    ) -> List[TrainingMetricsRecord]:
        """Aggregate daily workout data into training metrics by sport.
        
        Args:
            target_date: Date to aggregate data for
            workout_records: Workout data for the date
            
        Returns:
            List of training metrics records (one per sport per day)
        """
        # Find workouts for target date
        daily_workouts = self._find_workouts_for_date(workout_records, target_date)
        
        if not daily_workouts:
            return [TrainingMetricsRecord(
                date=target_date,
                day=target_date.strftime("%a"),
                sport=None,
                duration=None,
                workout_count=0,
            )]
        
        # Group workouts by sport_type
        workouts_by_sport_type = self._group_workouts_by_sport_type(daily_workouts)
        
        # Create one record per sport_type
        training_records = []
        for sport_type, sport_workouts in workouts_by_sport_type.items():
            # Calculate metrics for this sport_type
            total_duration = sum(w.duration_minutes for w in sport_workouts)
            
            training_records.append(TrainingMetricsRecord(
                date=target_date,
                day=target_date.strftime("%a"),
                sport=sport_type,
                duration=total_duration,
                workout_count=len(sport_workouts),
            ))
        
        # Sort by duration (longest first) for consistent ordering
        training_records.sort(key=lambda x: x.duration or 0, reverse=True)
        
        return training_records
    
    def _find_workouts_for_date(self, records: List[WorkoutRecord], target_date: date) -> List[WorkoutRecord]:
        """Find all workout records for specific date."""
        return [record for record in records if record.date == target_date]
    
    def _group_workouts_by_sport_type(self, workouts: List[WorkoutRecord]) -> dict:
        """Group workouts by sport_type."""
        workouts_by_sport_type = {}
        for workout in workouts:
            sport_type = workout.sport_type
            if sport_type not in workouts_by_sport_type:
                workouts_by_sport_type[sport_type] = []
            workouts_by_sport_type[sport_type].append(workout)
        return workouts_by_sport_type
    


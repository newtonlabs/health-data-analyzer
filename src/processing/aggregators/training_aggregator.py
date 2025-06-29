"""Training aggregator for combining workout and training load data."""

from datetime import date
from typing import List

from src.models.raw_data import WorkoutRecord
from src.models.aggregations import TrainingMetricsRecord
from src.models.enums import SportType, DataSource


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
                title=None,
            )]
        
        # Apply business logic filters and create training records
        training_records = []
        
        # Process strength workouts (from Hevy only)
        strength_workouts = [
            w for w in daily_workouts 
            if w.sport_type == SportType.STRENGTH_TRAINING and w.source == DataSource.HEVY
        ]
        if strength_workouts:
            total_duration = sum(w.duration_minutes for w in strength_workouts)
            # Use the title from the first (or longest) strength workout
            primary_workout = max(strength_workouts, key=lambda w: w.duration_minutes or 0)
            
            training_records.append(TrainingMetricsRecord(
                date=target_date,
                day=target_date.strftime("%a"),
                sport=SportType.STRENGTH_TRAINING,
                duration=total_duration,
                title=primary_workout.title,
            ))
        
        # Process cardio workouts (from Whoop only)
        cardio_workouts = [
            w for w in daily_workouts 
            if w.sport_type == SportType.CARDIO and w.source == DataSource.WHOOP
        ]
        if cardio_workouts:
            total_duration = sum(w.duration_minutes for w in cardio_workouts)
            # Use sport_name as title for cardio workouts
            primary_workout = max(cardio_workouts, key=lambda w: w.duration_minutes or 0)
            
            training_records.append(TrainingMetricsRecord(
                date=target_date,
                day=target_date.strftime("%a"),
                sport=SportType.CARDIO,
                duration=total_duration,
                title=primary_workout.sport_name,  # Use sport_name as title for cardio
            ))
        
        # Ignore walking workouts as requested
        
        # Sort by duration (longest first) for consistent ordering
        training_records.sort(key=lambda x: x.duration or 0, reverse=True)
        
        return training_records
    
    def _find_workouts_for_date(self, records: List[WorkoutRecord], target_date: date) -> List[WorkoutRecord]:
        """Find all workout records for specific date."""
        return [record for record in records if record.date == target_date]
    

    


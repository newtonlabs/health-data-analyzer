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
                strain=None,
                workout_count=0,
                calories_burned=None,
            )]
        
        # Group workouts by sport
        workouts_by_sport = self._group_workouts_by_sport(daily_workouts)
        
        # Create one record per sport
        training_records = []
        for sport, sport_workouts in workouts_by_sport.items():
            # Calculate metrics for this sport
            total_duration = sum(w.duration_minutes for w in sport_workouts)
            total_calories = sum(w.calories for w in sport_workouts if w.calories)
            avg_strain = sum(w.strain_score for w in sport_workouts if w.strain_score) / len([w for w in sport_workouts if w.strain_score]) if any(w.strain_score for w in sport_workouts) else None
            
            training_records.append(TrainingMetricsRecord(
                date=target_date,
                day=target_date.strftime("%a"),
                sport=sport,
                duration=total_duration,
                strain=avg_strain,
                workout_count=len(sport_workouts),
                calories_burned=total_calories if total_calories > 0 else None,
            ))
        
        # Sort by duration (longest first) for consistent ordering
        training_records.sort(key=lambda x: x.duration or 0, reverse=True)
        
        return training_records
    
    def _find_workouts_for_date(self, records: List[WorkoutRecord], target_date: date) -> List[WorkoutRecord]:
        """Find all workout records for specific date."""
        return [record for record in records if record.date == target_date]
    
    def _group_workouts_by_sport(self, workouts: List[WorkoutRecord]) -> dict:
        """Group workouts by sport type."""
        workouts_by_sport = {}
        for workout in workouts:
            sport = workout.sport_type
            if sport not in workouts_by_sport:
                workouts_by_sport[sport] = []
            workouts_by_sport[sport].append(workout)
        return workouts_by_sport
    


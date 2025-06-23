"""Module for generating health and fitness metrics."""

from datetime import datetime
from typing import Any

import pandas as pd

from src.utils.logging_utils import HealthLogger

from .aggregators.macros_activity import MacrosActivityAggregator
from .aggregators.recovery import RecoveryAggregator
from .aggregators.training import TrainingAggregator
from .processor import Processor


class Aggregator:
    """Generate health and fitness metrics from processed data.

    This class orchestrates different aggregators to generate metrics
    for reporting and visualization. Each aggregator focuses on a specific
    domain of metrics:

    1. MacrosActivityAggregator: Combines nutrition, activity, steps, and weight data
    2. RecoveryAggregator: Processes recovery and resilience metrics
    3. TrainingAggregator: Handles workout and training data

    The class provides a clean interface for accessing these metrics
    while delegating the implementation details to the specialized aggregators.
    """

    def __init__(self, processor: Processor):
        """Initialize Aggregator with specialized aggregators.

        Args:
            processor: Processor instance to use for data
        """
        self.processor = processor
        self.logger = HealthLogger(__name__)

        # Initialize aggregators
        self.macros_activity = MacrosActivityAggregator(processor)
        self.recovery = RecoveryAggregator(processor)
        self.training = TrainingAggregator(processor)

    def weekly_macros_and_activity(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Get weekly macros and activity metrics.

        Delegates to MacrosActivityAggregator to combine nutrition, activity,
        steps, and weight data into a single DataFrame.

        Args:
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            DataFrame with macros and activity metrics
        """
        return self.macros_activity.weekly_macros_and_activity(start_date, end_date)

    def recovery_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Get recovery metrics for date range.

        Delegates to RecoveryAggregator to process recovery and resilience data.

        Args:
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            DataFrame with recovery metrics
        """
        return self.recovery.get_recovery_metrics(start_date, end_date)

    def training_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Get training metrics for date range.

        Delegates to TrainingAggregator to process workout data.

        Args:
            start_date: Start date for filtering data
            end_date: End date for filtering data

        Returns:
            DataFrame with training metrics
        """
        return self.training.get_training_metrics(start_date, end_date)

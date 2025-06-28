"""Processing component registry for transformers and aggregators."""

from typing import Dict, List, Optional, Any
from .transformers.workout_transformer import WorkoutTransformer
from .transformers.activity_transformer import ActivityTransformer
from .transformers.weight_transformer import WeightTransformer
from .transformers.recovery_transformer import RecoveryTransformer
from .transformers.sleep_transformer import SleepTransformer
from .transformers.exercise_transformer import ExerciseTransformer
from .transformers.nutrition_transformer import NutritionTransformer
from .transformers.resilience_transformer import ResilienceTransformer
from .aggregators.recovery_aggregator import RecoveryAggregator
from .aggregators.macros_activity_aggregator import MacrosActivityAggregator
from .aggregators.training_aggregator import TrainingAggregator


class ProcessorRegistry:
    """Registry for managing transformers and aggregators with their capabilities."""
    
    def __init__(self):
        """Initialize registry and register all components."""
        self.transformers: Dict[str, Any] = {}
        self.aggregators: Dict[str, Any] = {}
        self._register_all_components()
    
    def _register_all_components(self):
        """Register all transformers and aggregators."""
        # Register transformers - clean naming, no _records suffix needed
        self.register_transformer('workouts', WorkoutTransformer(), ['workouts'])
        self.register_transformer('activity', ActivityTransformer(), ['activity'])
        self.register_transformer('weight', WeightTransformer(), ['weight'])
        self.register_transformer('recovery', RecoveryTransformer(), ['recovery'])
        self.register_transformer('sleep', SleepTransformer(), ['sleep'])
        self.register_transformer('exercise', ExerciseTransformer(), ['exercises'])
        self.register_transformer('nutrition', NutritionTransformer(), ['nutrition'])
        self.register_transformer('resilience', ResilienceTransformer(), ['resilience'])
        
        # Register aggregators
        self.register_aggregator('recovery', RecoveryAggregator(), ['recovery', 'sleep', 'resilience'])
        self.register_aggregator('macros', MacrosActivityAggregator(), ['nutrition', 'activity', 'weight'])
        self.register_aggregator('training', TrainingAggregator(), ['workouts'])
    
    def register_transformer(self, output_key: str, transformer: Any, input_types: List[str]):
        """Register a transformer with its capabilities.
        
        Args:
            output_key: The key to use for transformed data storage
            transformer: The transformer instance
            input_types: List of data types this transformer can handle
        """
        self.transformers[output_key] = {
            'instance': transformer,
            'input_types': input_types,
            'output_key': output_key
        }
    
    def register_aggregator(self, name: str, aggregator: Any, required_data: List[str]):
        """Register an aggregator with its data requirements.
        
        Args:
            name: Name of the aggregator
            aggregator: The aggregator instance
            required_data: List of data types this aggregator requires
        """
        self.aggregators[name] = {
            'instance': aggregator,
            'required_data': required_data
        }
    
    def get_transformer_for_data_type(self, data_type: str) -> Optional[Dict[str, Any]]:
        """Find transformer that can handle the given data type.
        
        Args:
            data_type: The data type to find a transformer for
            
        Returns:
            Dictionary with transformer info or None if not found
        """
        for transformer_info in self.transformers.values():
            if data_type in transformer_info['input_types']:
                return transformer_info
        return None
    
    def get_aggregator(self, name: str) -> Optional[Dict[str, Any]]:
        """Get aggregator by name.
        
        Args:
            name: Name of the aggregator
            
        Returns:
            Dictionary with aggregator info or None if not found
        """
        return self.aggregators.get(name)
    
    def collect_data_for_aggregator(self, aggregator_name: str, transformed_data: Dict[str, Dict[str, List]]) -> Dict[str, List]:
        """Collect data required by an aggregator from transformed data.
        
        Args:
            aggregator_name: Name of the aggregator
            transformed_data: Transformed data organized by service and data type
            
        Returns:
            Dictionary mapping data types to collected records
        """
        aggregator_info = self.get_aggregator(aggregator_name)
        if not aggregator_info:
            return {}
        
        collected_data = {}
        required_types = aggregator_info['required_data']
        
        # Collect data of each required type from all services
        for data_type in required_types:
            collected_data[data_type] = []
            for service_data in transformed_data.values():
                if data_type in service_data:
                    collected_data[data_type].extend(service_data[data_type])
        
        return collected_data
    
    def get_all_aggregator_names(self) -> List[str]:
        """Get list of all registered aggregator names."""
        return list(self.aggregators.keys())

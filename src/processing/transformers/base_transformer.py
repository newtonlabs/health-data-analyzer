"""Base class for data transformers.

This module provides the base class for all data transformer implementations,
defining the common interface and shared functionality for normalizing,
cleaning, and validating structured data records.
"""

from abc import ABC, abstractmethod
from typing import List, Any, Dict, Optional, TypeVar, Generic
from datetime import datetime, date

from src.models.collections import ProcessedDataCollection
from src.utils.logging_utils import HealthLogger

# Generic type for transformer input/output
T = TypeVar('T')


class BaseTransformer(ABC, Generic[T]):
    """Base class for all data transformers.
    
    Transformers are responsible for normalizing, cleaning, and validating
    structured data records. They should ensure data consistency and quality
    across all sources.
    """
    
    def __init__(self):
        """Initialize the transformer."""
        self.logger = HealthLogger(self.__class__.__name__)
    
    @abstractmethod
    def transform(self, data: T) -> T:
        """Transform the input data.
        
        Args:
            data: Input data to transform
            
        Returns:
            Transformed data of the same type
        """
        pass
    
    def validate_data(self, data: T) -> bool:
        """Validate data before transformation.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        return data is not None
    
    def log_transformation(
        self, 
        operation: str, 
        input_count: int, 
        output_count: int,
        details: Optional[str] = None
    ) -> None:
        """Log transformation operation for monitoring.
        
        Args:
            operation: Description of the transformation operation
            input_count: Number of input records
            output_count: Number of output records
            details: Additional details about the transformation
        """
        log_msg = f"{operation}: {input_count} -> {output_count} records"
        if details:
            log_msg += f" ({details})"
        
        self.logger.info(log_msg)


class DataCollectionTransformer(BaseTransformer[ProcessedDataCollection]):
    """Base class for transformers that work on entire data collections.
    
    This is useful for transformers that need to process multiple record types
    or perform cross-record analysis and normalization.
    """
    
    def transform_workouts(self, collection: ProcessedDataCollection) -> ProcessedDataCollection:
        """Transform workout records in the collection.
        
        Args:
            collection: Data collection to transform
            
        Returns:
            Collection with transformed workout records
        """
        return collection  # Default: no transformation
    
    def transform_recovery(self, collection: ProcessedDataCollection) -> ProcessedDataCollection:
        """Transform recovery records in the collection.
        
        Args:
            collection: Data collection to transform
            
        Returns:
            Collection with transformed recovery records
        """
        return collection  # Default: no transformation
    
    def transform_sleep(self, collection: ProcessedDataCollection) -> ProcessedDataCollection:
        """Transform sleep records in the collection.
        
        Args:
            collection: Data collection to transform
            
        Returns:
            Collection with transformed sleep records
        """
        return collection  # Default: no transformation
    
    def transform_weight(self, collection: ProcessedDataCollection) -> ProcessedDataCollection:
        """Transform weight records in the collection.
        
        Args:
            collection: Data collection to transform
            
        Returns:
            Collection with transformed weight records
        """
        return collection  # Default: no transformation
    
    def transform_nutrition(self, collection: ProcessedDataCollection) -> ProcessedDataCollection:
        """Transform nutrition records in the collection.
        
        Args:
            collection: Data collection to transform
            
        Returns:
            Collection with transformed nutrition records
        """
        return collection  # Default: no transformation
    
    def transform_activity(self, collection: ProcessedDataCollection) -> ProcessedDataCollection:
        """Transform activity records in the collection.
        
        Args:
            collection: Data collection to transform
            
        Returns:
            Collection with transformed activity records
        """
        return collection  # Default: no transformation


class RecordListTransformer(BaseTransformer[List[T]], Generic[T]):
    """Base class for transformers that work on lists of records.
    
    This is useful for transformers that process individual record types
    independently.
    """
    
    def transform_record(self, record: T) -> Optional[T]:
        """Transform a single record.
        
        Args:
            record: Record to transform
            
        Returns:
            Transformed record or None if record should be filtered out
        """
        return record  # Default: no transformation
    
    def transform(self, records: List[T]) -> List[T]:
        """Transform a list of records.
        
        Args:
            records: List of records to transform
            
        Returns:
            List of transformed records
        """
        if not self.validate_data(records):
            return []
        
        transformed = []
        filtered_count = 0
        
        for record in records:
            transformed_record = self.transform_record(record)
            if transformed_record is not None:
                transformed.append(transformed_record)
            else:
                filtered_count += 1
        
        # Log transformation statistics
        self.log_transformation(
            f"Transform {self.__class__.__name__}",
            len(records),
            len(transformed),
            f"{filtered_count} filtered" if filtered_count > 0 else None
        )
        
        return transformed
    
    def filter_record(self, record: T) -> bool:
        """Determine if a record should be kept.
        
        Args:
            record: Record to evaluate
            
        Returns:
            True if record should be kept, False to filter out
        """
        return True  # Default: keep all records
    
    def validate_record(self, record: T) -> bool:
        """Validate a single record.
        
        Args:
            record: Record to validate
            
        Returns:
            True if record is valid, False otherwise
        """
        return record is not None


class ValidationTransformer(RecordListTransformer[T], Generic[T]):
    """Base class for validation-focused transformers.
    
    These transformers focus on data quality validation and filtering
    rather than data modification.
    """
    
    def __init__(self, strict_mode: bool = False):
        """Initialize the validation transformer.
        
        Args:
            strict_mode: If True, invalid records cause exceptions.
                        If False, invalid records are filtered out.
        """
        super().__init__()
        self.strict_mode = strict_mode
        self.validation_errors: List[str] = []
    
    def transform_record(self, record: T) -> Optional[T]:
        """Validate and optionally transform a record.
        
        Args:
            record: Record to validate/transform
            
        Returns:
            Record if valid, None if invalid (in non-strict mode)
            
        Raises:
            ValueError: If record is invalid and strict_mode is True
        """
        if not self.validate_record(record):
            error_msg = f"Invalid record: {record}"
            self.validation_errors.append(error_msg)
            
            if self.strict_mode:
                raise ValueError(error_msg)
            else:
                self.logger.warning(error_msg)
                return None
        
        return record
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results.
        
        Returns:
            Dictionary containing validation statistics
        """
        return {
            "total_errors": len(self.validation_errors),
            "strict_mode": self.strict_mode,
            "errors": self.validation_errors[-10:]  # Last 10 errors
        }

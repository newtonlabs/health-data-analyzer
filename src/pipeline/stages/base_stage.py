"""Base classes for pipeline stages."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Any, Optional
from enum import Enum


class StageStatus(Enum):
    """Status of a pipeline stage execution."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


@dataclass
class StageResult:
    """Result of a pipeline stage execution."""
    stage_name: str
    status: StageStatus
    data: Dict[str, Any] = field(default_factory=dict)
    file_paths: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class PipelineContext:
    """Context object passed between pipeline stages."""
    # Configuration
    start_date: date
    end_date: date
    services: List[str]
    enable_csv: bool = True
    debug_mode: bool = False
    
    # Data flow between stages
    raw_data: Dict[str, Any] = field(default_factory=dict)
    extracted_data: Dict[str, Dict[str, List]] = field(default_factory=dict)
    transformed_data: Dict[str, Dict[str, List]] = field(default_factory=dict)
    aggregated_data: Dict[str, List] = field(default_factory=dict)
    
    # File tracking
    file_paths: Dict[str, str] = field(default_factory=dict)
    
    # Execution tracking
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    
    def add_stage_result(self, result: StageResult) -> None:
        """Add a stage result to the context."""
        self.stage_results[result.stage_name] = result
        
        # Merge file paths
        self.file_paths.update(result.file_paths)
    
    def get_days_count(self) -> int:
        """Get the number of days in the date range."""
        return (self.end_date - self.start_date).days + 1
    
    def is_service_enabled(self, service: str) -> bool:
        """Check if a service is enabled for processing."""
        return service.lower() in [s.lower() for s in self.services]


class PipelineStage(ABC):
    """Base class for all pipeline stages."""
    
    def __init__(self, stage_name: str):
        """Initialize the pipeline stage.
        
        Args:
            stage_name: Name of this stage
        """
        self.stage_name = stage_name
        from src.utils.logging_utils import HealthLogger
        self.logger = HealthLogger(f"Stage.{stage_name}")
    
    @abstractmethod
    def execute(self, context: PipelineContext) -> StageResult:
        """Execute this pipeline stage.
        
        Args:
            context: Pipeline context with data and configuration
            
        Returns:
            StageResult with execution results
        """
        pass
    
    def _create_success_result(self, data: Dict[str, Any] = None, 
                             file_paths: Dict[str, str] = None,
                             metrics: Dict[str, Any] = None) -> StageResult:
        """Create a successful stage result."""
        return StageResult(
            stage_name=self.stage_name,
            status=StageStatus.SUCCESS,
            data=data or {},
            file_paths=file_paths or {},
            metrics=metrics or {}
        )
    
    def _create_error_result(self, error: str, 
                           data: Dict[str, Any] = None) -> StageResult:
        """Create a failed stage result."""
        return StageResult(
            stage_name=self.stage_name,
            status=StageStatus.FAILED,
            data=data or {},
            error=error
        )
    
    def _create_partial_result(self, data: Dict[str, Any] = None,
                              file_paths: Dict[str, str] = None,
                              metrics: Dict[str, Any] = None,
                              error: str = None) -> StageResult:
        """Create a partial success stage result."""
        return StageResult(
            stage_name=self.stage_name,
            status=StageStatus.PARTIAL,
            data=data or {},
            file_paths=file_paths or {},
            metrics=metrics or {},
            error=error
        )

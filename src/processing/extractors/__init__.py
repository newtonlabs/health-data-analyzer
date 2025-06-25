"""Data extractors for converting raw API responses to structured records.

This module contains extractor classes that convert raw API responses
into structured data records using the data models.
"""

from .base_extractor import BaseExtractor
from .whoop_extractor import WhoopExtractor

__all__ = [
    'BaseExtractor',
    'WhoopExtractor'
]

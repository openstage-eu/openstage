"""
openstage: EU legislative data models and adapters

A Python package for working with EU legislative data:
- Typed Pydantic models for procedures, events, and documents
- Adapters for mapping external data into typed models

Architecture:
- openstage: Data models and adapters (this package)
- openbasement: RDF parsing from EU Cellar data
- openstage-infrastructure: Workflow orchestration, data collection, storage, and publishing

Usage:
    from openstage.models import Procedure
"""

__version__ = "0.0.0"
__author__ = "Maximilian Haag"

from . import models

__all__ = [
    "models",
]

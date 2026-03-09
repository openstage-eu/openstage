"""
openstage: EU legislative data models and adapters

A Python package for working with EU legislative data:
- Typed Pydantic models for procedures, events, and documents
- Adapters for mapping external data into typed models
- Collection utilities and dataset I/O

Architecture:
- openstage: Data models and adapters (this package)
- openbasement: RDF parsing from EU Cellar data
- openstage-infrastructure: Workflow orchestration, data collection, storage, and publishing

Usage:
    from openstage.models import Procedure
    from openstage.collections import ProcedureList
    from openstage.dataset import Dataset
"""

__version__ = "0.0.0"
__author__ = "Maximilian Haag"

from . import models
from .collections import (
    ProcedureList,
    open_at,
    backlog_at,
    filter_procedures,
)
from .dataset import Dataset, register_dataset

__all__ = [
    "models",
    "ProcedureList",
    "Dataset",
    "register_dataset",
    "open_at",
    "backlog_at",
    "filter_procedures",
]

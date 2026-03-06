"""EU-specific case models with typed domain fields.

These subclasses declare known EU legislative fields with rich metadata
(variable types, controlled vocabularies, data sources) so they appear in
model_json_schema() and enable codebook generation.
"""

from __future__ import annotations

from .document import EUDocument
from .event import EUEvent
from .procedure import EUProcedure

__all__ = [
    "EUDocument",
    "EUEvent",
    "EUProcedure",
]

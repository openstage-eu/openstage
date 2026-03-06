"""EU integration tests: openbasement RDF extraction -> openstage EU adapter -> typed models.

Runs the full pipeline against all 1000 openbasement EU Cellar RDF fixtures.
Skipped automatically if openbasement is not installed.
"""

from __future__ import annotations

import pytest

try:
    from openbasement import extract  # noqa: F401

    HAS_OPENBASEMENT = True
except ImportError:
    HAS_OPENBASEMENT = False

pytestmark = pytest.mark.skipif(
    not HAS_OPENBASEMENT, reason="openbasement not installed"
)

from openstage.adapters.eu.procedures import procedure_from_openbasement
from openstage.models import Procedure, Event, Document


class TestEUAdapterAcceptance:
    """Every openbasement EU fixture must convert to a valid Procedure without error."""

    def test_adapter_succeeds(self, procedure_dict):
        proc = procedure_from_openbasement(procedure_dict)
        assert isinstance(proc, Procedure)

    def test_identifiers_non_empty(self, procedure_dict):
        proc = procedure_from_openbasement(procedure_dict)
        assert len(proc.identifiers) > 0

    def test_title_has_language(self, procedure_dict):
        proc = procedure_from_openbasement(procedure_dict)
        if proc.title is not None:
            assert len(proc.title.languages) > 0

    def test_events_are_typed(self, procedure_dict):
        proc = procedure_from_openbasement(procedure_dict)
        for event in proc.events:
            assert isinstance(event, Event)

    def test_documents_are_typed(self, procedure_dict):
        proc = procedure_from_openbasement(procedure_dict)
        for doc in proc.get_all_documents():
            assert isinstance(doc, Document)

    def test_nested_documents_in_events(self, procedure_dict):
        proc = procedure_from_openbasement(procedure_dict)
        for event in proc.events:
            for doc in event.documents:
                assert isinstance(doc, Document)

    def test_serialization_roundtrip(self, procedure_dict):
        proc = procedure_from_openbasement(procedure_dict)
        data = proc.model_dump()
        proc2 = Procedure.model_validate(data)
        assert isinstance(proc2, Procedure)
        assert len(proc2.identifiers) == len(proc.identifiers)

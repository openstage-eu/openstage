"""Tests for the EU adapter mapping openbasement output to openstage models."""

import pytest

from openstage.adapters.eu.procedures import (
    procedure_from_openbasement,
    _identifiers_from_uris,
    _scheme_from_uri,
)


# Realistic openbasement output fixture (based on actual eu_procedure template results)
PROCEDURE_FIXTURE = {
    "_uri": "http://publications.europa.eu/resource/procedure/2019_2026",
    "_same_as": [
        "http://publications.europa.eu/resource/cellar/abc-123-def",
        "http://publications.europa.eu/resource/pegase/PE-2019-0089",
    ],
    "_rdf_types": [
        "http://publications.europa.eu/ontology/cdm#procedure_codecision",
        "http://publications.europa.eu/ontology/cdm#procedure",
    ],
    "_raw_triples": [
        (
            "http://publications.europa.eu/resource/procedure/2019_2026",
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
            "http://publications.europa.eu/ontology/cdm#procedure_codecision",
        ),
    ],
    "title": {
        "en": "Regulation on transparency and targeting of political advertising",
        "fr": "Reglement sur la transparence et le ciblage de la publicite a caractere politique",
        "de": "Verordnung uber die Transparenz und das Targeting politischer Werbung",
    },
    "reference": "2021/0381/COD",
    "date": "2023-03-30",
    "procedure_type": "OLP",
    "subject_matters": [
        "http://eurovoc.europa.eu/5283",
        "http://eurovoc.europa.eu/1759",
    ],
    "basis_legal": "http://publications.europa.eu/resource/celex/12016E294",
    "year_procedure": "2021",
    "number_procedure": "0381",
    "events": [
        {
            "_uri": "http://publications.europa.eu/resource/cellar/event-001",
            "_same_as": [],
            "date": "2021-11-25",
            "type_code": "PROP_INIT",
            "title": {"en": "Legislative proposal published"},
            "initiated_by_institution": "COM",
            "documents": [
                {
                    "_uri": "http://publications.europa.eu/resource/cellar/doc-001",
                    "title": {"en": "Proposal for a Regulation", "fr": "Proposition de reglement"},
                    "date": "2021-11-25",
                },
            ],
            "works": [
                {
                    "_uri": "http://publications.europa.eu/resource/celex/52021PC0731",
                    "title": {"en": "COM(2021) 731 final"},
                },
            ],
            "document_reference": ["COM/2021/731/FINAL"],
        },
        {
            "_uri": "http://publications.europa.eu/resource/cellar/event-002",
            "date": "2023-02-02",
            "type_code": "POSITION_EP",
            "title": {"en": "European Parliament position"},
            "occurs_in_phase": "RDG1",
            "document_reference": ["PE/70/2023/INIT"],
        },
    ],
    "documents": [
        {
            "_uri": "http://publications.europa.eu/resource/cellar/doc-top-001",
            "title": {"en": "Final act"},
            "date": "2024-03-13",
            "doc_number": "2024/900",
        },
    ],
}


class TestSchemeFromUri:

    def test_cellar(self):
        assert _scheme_from_uri("http://publications.europa.eu/resource/cellar/abc-123") == "cellar"

    def test_procedure(self):
        assert _scheme_from_uri("http://publications.europa.eu/resource/procedure/2019_2026") == "procedure_ref"

    def test_celex(self):
        assert _scheme_from_uri("http://publications.europa.eu/resource/celex/32016R0679") == "celex"

    def test_pegase(self):
        assert _scheme_from_uri("http://publications.europa.eu/resource/pegase/PE-123") == "pegase"

    def test_eli(self):
        assert _scheme_from_uri("http://data.europa.eu/eli/reg/2016/679/oj") == "eli"

    def test_unknown_falls_back_to_uri(self):
        assert _scheme_from_uri("http://example.com/something") == "uri"


class TestIdentifiersFromUris:

    def test_primary_and_same_as(self):
        ids = _identifiers_from_uris(
            "http://publications.europa.eu/resource/procedure/2019_2026",
            ["http://publications.europa.eu/resource/cellar/abc-123"],
        )
        assert ids.get("procedure_ref") == "2019_2026"
        assert ids.get("cellar") == "abc-123"

    def test_none_uri(self):
        ids = _identifiers_from_uris(None, None)
        assert len(ids) == 0


class TestProcedureFromOpenbasement:

    def test_identifiers(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        assert proc.identifiers.get("procedure_ref") is not None
        assert proc.identifiers.get("cellar") == "abc-123-def"
        assert proc.identifiers.get("pegase") == "PE-2019-0089"
        # reference field also added as procedure_ref
        assert "2021/0381/COD" in proc.identifiers.get_all("procedure_ref")

    def test_title(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        assert proc.title is not None
        assert "transparency" in proc.title["en"].lower()
        assert proc.title["fr"] is not None
        assert str(proc.title) == proc.title["en"]  # English preferred

    def test_date_in_extras(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        assert proc.date == "2023-03-30"

    def test_extra_fields(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        assert proc.procedure_type == "OLP"
        assert len(proc.subject_matters) == 2
        assert proc.basis_legal is not None
        assert proc.year_procedure == "2021"

    def test_raw_metadata(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        assert "_rdf_types" in proc._raw
        assert "_raw_triples" in proc._raw
        assert len(proc._raw["_rdf_types"]) == 2

    def test_events(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        assert len(proc.events) == 2

        e0 = proc.events[0]
        assert e0.date == "2021-11-25"
        assert e0.type == "PROP_INIT"
        assert "proposal" in str(e0.title).lower()
        assert e0.initiated_by_institution == "COM"

        e1 = proc.events[1]
        assert e1.type == "POSITION_EP"
        assert e1.occurs_in_phase == "RDG1"

    def test_event_documents(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        e0 = proc.events[0]
        # 1 document + 1 work + 1 document_reference
        assert len(e0.documents) == 3
        assert e0.documents[0].title is not None
        assert "fr" in e0.documents[0].title.languages

    def test_event_document_reference_stubs(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        e0 = proc.events[0]
        # Last document is the stub from document_reference
        ref_doc = e0.documents[-1]
        assert ref_doc.identifiers.get("doc_ref") == "COM/2021/731/FINAL"
        assert ref_doc.title is None

        # Event 1 has only a document_reference, no works
        e1 = proc.events[1]
        assert len(e1.documents) == 1
        assert e1.documents[0].identifiers.get("doc_ref") == "PE/70/2023/INIT"

    def test_get_all_documents(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        all_docs = proc.get_all_documents()
        # event 0: 1 document + 1 work + 1 ref; event 1: 1 ref
        assert len(all_docs) == 4

    def test_serialization_roundtrip(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        data = proc.model_dump()

        # Title serializes as dict
        assert isinstance(data["title"], dict)
        assert "en" in data["title"]

        # Identifiers serialize as list of dicts
        assert isinstance(data["identifiers"], list)
        assert all(isinstance(i, dict) for i in data["identifiers"])

        # Extra fields are top-level
        assert "procedure_type" in data
        assert "ext" not in data

        # _raw is excluded
        assert "_raw" not in data

        # Can reconstruct
        proc2 = type(proc).model_validate(data)
        assert str(proc2.title) == str(proc.title)
        assert proc2.procedure_type == "OLP"

    def test_empty_input(self):
        proc = procedure_from_openbasement({})
        assert proc.title is None
        assert proc.events == []
        assert proc.get_all_documents() == []
        assert len(proc.identifiers) == 0

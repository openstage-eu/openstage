"""Tests for EU case models, field metadata, and codebook extraction."""

import warnings

import pytest

from openstage.models import extract_codebook, codebook_to_markdown
from openstage.models.eu import EUProcedure, EUEvent, EUDocument
from openstage.adapters.eu.procedures import procedure_from_openbasement

# Reuse the realistic fixture from test_adapters_eu
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
                    "title": {
                        "en": "Proposal for a Regulation",
                        "fr": "Proposition de reglement",
                    },
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
            "occurs_in_phase": "FIRST_READING",
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


class TestEUDocumentConstruction:

    def test_basic(self):
        doc = EUDocument()
        assert doc.title is None
        assert doc.date is None
        assert doc.doc_number is None

    def test_with_fields(self):
        doc = EUDocument(doc_number="2024/900", date="2024-03-13")
        assert doc.doc_number == "2024/900"
        assert doc.date == "2024-03-13"

    def test_from_openbasement(self):
        data = PROCEDURE_FIXTURE["documents"][0]
        doc = EUDocument.from_openbasement(data)
        assert doc.date == "2024-03-13"
        assert doc.doc_number == "2024/900"
        assert doc.identifiers.get("cellar") is not None


class TestEUEventConstruction:

    def test_basic(self):
        event = EUEvent()
        assert event.initiated_by_institution is None
        assert event.occurs_in_phase is None

    def test_from_openbasement(self):
        data = PROCEDURE_FIXTURE["events"][0]
        event = EUEvent.from_openbasement(data)
        assert event.date == "2021-11-25"
        assert event.type == "PROP_INIT"
        assert event.initiated_by_institution == "COM"
        # documents + works + document_reference
        assert len(event.documents) == 3
        assert all(isinstance(d, EUDocument) for d in event.documents)

    def test_from_openbasement_with_phase(self):
        data = PROCEDURE_FIXTURE["events"][1]
        event = EUEvent.from_openbasement(data)
        assert event.occurs_in_phase == "FIRST_READING"


class TestEUProcedureConstruction:

    def test_basic(self):
        proc = EUProcedure()
        assert proc.procedure_type is None
        assert proc.subject_matters == []
        assert proc.basis_legal is None

    def test_with_typed_fields(self):
        proc = EUProcedure(
            procedure_type="OLP",
            subject_matters=["http://eurovoc.europa.eu/5283"],
            year_procedure="2021",
        )
        assert proc.procedure_type == "OLP"
        assert len(proc.subject_matters) == 1
        assert proc.year_procedure == "2021"

    def test_from_openbasement(self):
        proc = EUProcedure.from_openbasement(PROCEDURE_FIXTURE)
        assert proc.procedure_type == "OLP"
        assert len(proc.subject_matters) == 2
        assert proc.basis_legal is not None
        assert proc.year_procedure == "2021"
        assert proc.number_procedure == "0381"
        assert proc.date == "2023-03-30"

    def test_from_openbasement_identifiers(self):
        proc = EUProcedure.from_openbasement(PROCEDURE_FIXTURE)
        assert proc.identifiers.get("procedure_ref") is not None
        assert proc.identifiers.get("cellar") == "abc-123-def"
        assert "2021/0381/COD" in proc.identifiers.get_all("procedure_ref")

    def test_from_openbasement_title(self):
        proc = EUProcedure.from_openbasement(PROCEDURE_FIXTURE)
        assert proc.title is not None
        assert "transparency" in proc.title["en"].lower()

    def test_from_openbasement_events(self):
        proc = EUProcedure.from_openbasement(PROCEDURE_FIXTURE)
        assert len(proc.events) == 2
        assert all(isinstance(e, EUEvent) for e in proc.events)
        assert proc.events[0].initiated_by_institution == "COM"

    def test_from_openbasement_get_all_documents(self):
        proc = EUProcedure.from_openbasement(PROCEDURE_FIXTURE)
        all_docs = proc.get_all_documents()
        # event 0: 1 document + 1 work + 1 ref; event 1: 1 ref
        assert len(all_docs) == 4
        assert all(isinstance(d, EUDocument) for d in all_docs)

    def test_start_event_finds_proposal(self):
        proc = EUProcedure.from_openbasement(PROCEDURE_FIXTURE)
        # Event 0 has type PROP_INIT which is not in _START_EVENT_TYPES,
        # but falls back to earliest by date
        assert proc.start_event is not None
        assert proc.start_date == "2021-11-25"

    def test_start_event_com_adoption(self):
        proc = EUProcedure(
            events=[
                EUEvent(date="2024-03-01", type="DIS_byCONSIL"),
                EUEvent(date="2024-01-01", type="ADP_byCOM"),
            ]
        )
        assert proc.start_event.type == "ADP_byCOM"

    def test_adoption_event(self):
        proc = EUProcedure(
            events=[
                EUEvent(date="2024-01-01", type="ADP_byCOM"),
                EUEvent(date="2024-06-01", type="ADP_FRM_byCONSIL"),
            ]
        )
        assert proc.adoption_event.type == "ADP_FRM_byCONSIL"
        assert proc.adoption_date == "2024-06-01"

    def test_adoption_event_none_when_ongoing(self):
        proc = EUProcedure(
            events=[
                EUEvent(date="2024-01-01", type="ADP_byCOM"),
            ]
        )
        assert proc.adoption_event is None
        assert proc.adoption_date is None

    def test_status_adopted(self):
        proc = EUProcedure(
            events=[
                EUEvent(type="Adoption formelle par Conseil"),
            ]
        )
        assert proc.status == "adopted"

    def test_withdrawal_event(self):
        proc = EUProcedure(
            events=[
                EUEvent(type="ADP_byCOM"),
                EUEvent(date="2024-05-01", type="Retrait par Commission"),
            ]
        )
        assert proc.withdrawal_event is not None
        assert proc.withdrawal_event.type == "Retrait par Commission"
        assert proc.withdrawal_date == "2024-05-01"

    def test_withdrawal_event_none(self):
        proc = EUProcedure(
            events=[
                EUEvent(type="ADP_byCOM"),
            ]
        )
        assert proc.withdrawal_event is None
        assert proc.withdrawal_date is None

    def test_status_withdrawn(self):
        proc = EUProcedure(
            events=[
                EUEvent(type="ADP_byCOM"),
                EUEvent(type="Retrait par Commission"),
            ]
        )
        assert proc.status == "withdrawn"

    def test_status_ongoing(self):
        proc = EUProcedure(
            events=[
                EUEvent(type="ADP_byCOM"),
                EUEvent(type="DIS_byCONSIL"),
            ]
        )
        assert proc.status == "ongoing"

    def test_status_empty(self):
        proc = EUProcedure()
        assert proc.status is None

    def test_from_openbasement_raw(self):
        proc = EUProcedure.from_openbasement(PROCEDURE_FIXTURE)
        assert "_rdf_types" in proc._raw

    def test_from_openbasement_empty(self):
        proc = EUProcedure.from_openbasement({})
        assert proc.title is None
        assert proc.events == []
        assert proc.get_all_documents() == []
        assert proc.procedure_type is None


class TestEUProcedureRoundtrip:

    def test_model_dump_and_validate(self):
        proc = EUProcedure.from_openbasement(PROCEDURE_FIXTURE)
        data = proc.model_dump()

        # Typed fields present at top level
        assert data["procedure_type"] == "OLP"
        assert len(data["subject_matters"]) == 2
        assert data["year_procedure"] == "2021"
        assert data["date"] == "2023-03-30"

        # _raw excluded
        assert "_raw" not in data

        # Roundtrip
        proc2 = EUProcedure.model_validate(data)
        assert proc2.procedure_type == "OLP"
        assert proc2.year_procedure == "2021"
        assert str(proc2.title) == str(proc.title)
        assert len(proc2.events) == 2


class TestModelJsonSchema:

    def test_eu_procedure_schema_has_x_annotations(self):
        schema = EUProcedure.model_json_schema()
        props = schema["properties"]

        # procedure_type should have x_variable_type
        pt = props["procedure_type"]
        # Could be in anyOf for Optional; check resolved
        resolved = _resolve_prop(pt)
        assert resolved.get("x_variable_type") == "nominal"
        assert "x_known_values" in resolved

    def test_eu_event_schema_has_x_annotations(self):
        schema = EUEvent.model_json_schema()
        props = schema["properties"]
        inst = _resolve_prop(props["initiated_by_institution"])
        assert inst.get("x_variable_type") == "nominal"

    def test_eu_document_schema_has_x_annotations(self):
        schema = EUDocument.model_json_schema()
        props = schema["properties"]
        dn = _resolve_prop(props["doc_number"])
        assert dn.get("x_variable_type") == "identifier"

    def test_base_fields_have_annotations(self):
        schema = EUProcedure.model_json_schema()
        props = schema["properties"]
        title = _resolve_prop(props["title"])
        assert title.get("x_variable_type") == "text"


def _resolve_prop(prop: dict) -> dict:
    """Helper to resolve anyOf in JSON Schema properties."""
    if "anyOf" in prop:
        for opt in prop["anyOf"]:
            if opt.get("type") != "null":
                merged = dict(opt)
                for k, v in prop.items():
                    if k != "anyOf":
                        merged[k] = v
                return merged
    return prop


class TestCodebook:

    def test_extract_codebook_has_all_fields(self):
        entries = extract_codebook(EUProcedure)
        names = {e["name"] for e in entries}
        # Base fields
        assert "title" in names
        assert "identifiers" in names
        # EU fields
        assert "procedure_type" in names
        assert "subject_matters" in names
        assert "basis_legal" in names

    def test_inherited_fields_marked(self):
        entries = extract_codebook(EUProcedure)
        by_name = {e["name"]: e for e in entries}
        # title is inherited from Procedure
        assert by_name["title"]["inherited_from"] == "Procedure"
        # procedure_type is own field
        assert by_name["procedure_type"]["inherited_from"] is None

    def test_x_metadata_present(self):
        entries = extract_codebook(EUProcedure)
        by_name = {e["name"]: e for e in entries}
        pt = by_name["procedure_type"]
        assert pt.get("x_variable_type") == "nominal"
        assert "OLP" in pt.get("x_known_values", {})

    def test_codebook_to_markdown(self):
        entries = extract_codebook(EUProcedure)
        md = codebook_to_markdown(entries)
        assert "# Codebook" in md
        assert "procedure_type" in md
        assert "Ordinary Legislative Procedure" in md
        assert "| Field |" in md


class TestSoftValidation:

    def test_known_value_no_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            EUProcedure(procedure_type="OLP")
            nominal_warnings = [x for x in w if "unknown value" in str(x.message)]
            assert len(nominal_warnings) == 0

    def test_unknown_value_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            EUProcedure(procedure_type="UNKNOWN_TYPE")
            nominal_warnings = [x for x in w if "unknown value" in str(x.message)]
            assert len(nominal_warnings) == 1
            assert "UNKNOWN_TYPE" in str(nominal_warnings[0].message)

    def test_none_value_no_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            EUProcedure(procedure_type=None)
            nominal_warnings = [x for x in w if "unknown value" in str(x.message)]
            assert len(nominal_warnings) == 0

    def test_event_known_institution_no_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            EUEvent(initiated_by_institution="COM")
            nominal_warnings = [x for x in w if "unknown value" in str(x.message)]
            assert len(nominal_warnings) == 0


class TestBackwardCompat:

    def test_procedure_from_openbasement_returns_eu_procedure(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        assert isinstance(proc, EUProcedure)

    def test_procedure_from_openbasement_typed_fields(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        assert proc.procedure_type == "OLP"
        assert proc.year_procedure == "2021"

    def test_procedure_from_openbasement_identifiers(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        assert proc.identifiers.get("cellar") == "abc-123-def"
        assert "2021/0381/COD" in proc.identifiers.get_all("procedure_ref")

    def test_procedure_from_openbasement_events(self):
        proc = procedure_from_openbasement(PROCEDURE_FIXTURE)
        assert len(proc.events) == 2
        assert proc.events[0].initiated_by_institution == "COM"

    def test_procedure_from_openbasement_empty(self):
        proc = procedure_from_openbasement({})
        assert proc.title is None
        assert proc.events == []
        assert proc.get_all_documents() == []


class TestMultiLangTextDefaultLang:

    def test_default_lang_underscore(self):
        from openstage.models import MultiLangText

        t = MultiLangText.from_value("hello")
        assert t["_"] == "hello"

    def test_custom_default_lang(self):
        from openstage.models import MultiLangText

        t = MultiLangText.from_value("hello", default_lang="en")
        assert t["en"] == "hello"
        assert "_" not in t

    def test_dict_ignores_default_lang(self):
        from openstage.models import MultiLangText

        t = MultiLangText.from_value({"fr": "bonjour"}, default_lang="en")
        assert t["fr"] == "bonjour"
        assert "en" not in t


class TestMultiLangTextJsonSchema:

    def test_json_schema_output(self):
        from openstage.models import MultiLangText

        schema = MultiLangText.__get_pydantic_json_schema__(None, None)
        assert schema["type"] == "object"
        assert "additionalProperties" in schema

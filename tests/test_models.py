"""Tests for openstage data models."""

import pytest

from openstage.models import (
    MultiLangText,
    Identifier,
    Identifiers,
    Entity,
    Document,
    Event,
    Procedure,
)


class TestMultiLangText:

    def test_from_dict(self):
        t = MultiLangText({"en": "Hello", "fr": "Bonjour"})
        assert t["en"] == "Hello"
        assert t["fr"] == "Bonjour"
        assert len(t) == 2

    def test_preferred_returns_english_first(self):
        t = MultiLangText({"fr": "Bonjour", "en": "Hello"})
        assert t.preferred() == "Hello"

    def test_preferred_fallback(self):
        t = MultiLangText({"de": "Hallo"})
        assert t.preferred() == "Hallo"
        assert t.preferred(("it",)) is None

    def test_str_returns_preferred(self):
        t = MultiLangText({"en": "Hello", "fr": "Bonjour"})
        assert str(t) == "Hello"

    def test_str_returns_first_if_no_preferred(self):
        t = MultiLangText({"bg": "Zdraveite"})
        assert str(t) == "Zdraveite"

    def test_empty(self):
        t = MultiLangText()
        assert not t
        assert len(t) == 0
        assert str(t) == ""

    def test_from_value_dict(self):
        t = MultiLangText.from_value({"en": "Hello"})
        assert t["en"] == "Hello"

    def test_from_value_str(self):
        t = MultiLangText.from_value("plain text")
        assert t["_"] == "plain text"

    def test_from_value_none(self):
        assert MultiLangText.from_value(None) is None

    def test_from_value_passthrough(self):
        original = MultiLangText({"en": "Hello"})
        assert MultiLangText.from_value(original) is original

    def test_get(self):
        t = MultiLangText({"en": "Hello"})
        assert t.get("en") == "Hello"
        assert t.get("fr") is None

    def test_languages(self):
        t = MultiLangText({"en": "Hello", "fr": "Bonjour"})
        assert set(t.languages) == {"en", "fr"}

    def test_items(self):
        t = MultiLangText({"en": "Hello"})
        assert list(t.items()) == [("en", "Hello")]

    def test_contains(self):
        t = MultiLangText({"en": "Hello"})
        assert "en" in t
        assert "fr" not in t

    def test_equality(self):
        a = MultiLangText({"en": "Hello"})
        b = MultiLangText({"en": "Hello"})
        assert a == b

    def test_pydantic_field_roundtrip(self):
        """MultiLangText works as a Pydantic field with serialization."""
        doc = Document(title=MultiLangText({"en": "Test"}))
        data = doc.model_dump()
        assert data["title"] == {"en": "Test"}

        doc2 = Document.model_validate(data)
        assert doc2.title["en"] == "Test"


class TestIdentifier:

    def test_basic(self):
        ident = Identifier(scheme="celex", value="32016R0679")
        assert ident.scheme == "celex"
        assert ident.value == "32016R0679"

    def test_frozen(self):
        ident = Identifier(scheme="celex", value="32016R0679")
        with pytest.raises(Exception):
            ident.scheme = "other"


class TestIdentifiers:

    def test_empty(self):
        ids = Identifiers()
        assert len(ids) == 0
        assert not ids

    def test_add_and_get(self):
        ids = Identifiers()
        ids.add("celex", "32016R0679")
        ids.add("cellar", "abc-123")
        assert ids.get("celex") == "32016R0679"
        assert ids.get("cellar") == "abc-123"
        assert ids.get("eli") is None

    def test_get_all(self):
        ids = Identifiers()
        ids.add("celex", "32016R0679")
        ids.add("celex", "32016R0680")
        assert ids.get_all("celex") == ["32016R0679", "32016R0680"]
        assert ids.get_all("eli") == []

    def test_schemes(self):
        ids = Identifiers()
        ids.add("celex", "a")
        ids.add("cellar", "b")
        ids.add("celex", "c")
        assert ids.schemes == ["celex", "cellar"]

    def test_iter(self):
        ids = Identifiers()
        ids.add("celex", "a")
        ids.add("cellar", "b")
        result = list(ids)
        assert len(result) == 2
        assert result[0].scheme == "celex"

    def test_pydantic_field_roundtrip(self):
        ids = Identifiers()
        ids.add("celex", "32016R0679")
        entity = Entity(identifiers=ids)
        data = entity.model_dump()
        assert data["identifiers"] == [{"scheme": "celex", "value": "32016R0679"}]

        entity2 = Entity.model_validate(data)
        assert entity2.identifiers.get("celex") == "32016R0679"


class TestEntity:

    def test_default_construction(self):
        e = Entity()
        assert len(e.identifiers) == 0
        assert e._raw == {}

    def test_raw_excluded_from_dump(self):
        e = Entity()
        e._raw = {"_raw_triples": [("s", "p", "o")]}
        data = e.model_dump()
        assert "_raw" not in data

    def test_extra_fields_accessible(self):
        e = Entity(procedure_type="OLP", year=2019)
        assert e.procedure_type == "OLP"
        assert e.year == 2019

    def test_extra_fields_in_model_extra(self):
        e = Entity(procedure_type="OLP", subject_matters=["trade"])
        assert e.model_extra == {
            "procedure_type": "OLP",
            "subject_matters": ["trade"],
        }

    def test_extra_fields_in_model_dump(self):
        e = Entity(procedure_type="OLP")
        data = e.model_dump()
        assert data["procedure_type"] == "OLP"

    def test_extra_fields_roundtrip(self):
        e = Entity(procedure_type="OLP", year=2019)
        data = e.model_dump()
        e2 = Entity.model_validate(data)
        assert e2.procedure_type == "OLP"
        assert e2.year == 2019


class TestDocument:

    def test_basic(self):
        doc = Document()
        assert doc.title is None
        assert doc.date is None

    def test_with_title(self):
        doc = Document(title=MultiLangText({"en": "A regulation"}))
        assert str(doc.title) == "A regulation"


class TestEvent:

    def test_basic(self):
        event = Event()
        assert event.date is None
        assert event.title is None
        assert event.type is None
        assert event.documents == []

    def test_with_documents(self):
        doc = Document(title=MultiLangText({"en": "Report"}))
        event = Event(
            date="2024-01-15",
            title=MultiLangText({"en": "Committee Vote"}),
            documents=[doc],
        )
        assert len(event.documents) == 1
        assert str(event.documents[0].title) == "Report"


class TestProcedure:

    def test_basic(self):
        proc = Procedure()
        assert proc.title is None
        assert proc.events == []

    def test_with_events(self):
        doc = Document(title=MultiLangText({"en": "Proposal"}))
        event = Event(date="2024-01-01", documents=[doc])
        proc = Procedure(
            title=MultiLangText({"en": "GDPR", "fr": "RGPD"}),
            events=[event],
        )
        assert str(proc.title) == "GDPR"
        assert proc.title["fr"] == "RGPD"
        assert len(proc.events) == 1

    def test_get_all_documents(self):
        doc1 = Document(title=MultiLangText({"en": "Proposal"}))
        doc2 = Document(title=MultiLangText({"en": "Report"}))
        doc3 = Document(title=MultiLangText({"en": "Amendment"}))
        proc = Procedure(
            events=[
                Event(date="2024-01-01", documents=[doc1, doc2]),
                Event(date="2024-02-01", documents=[doc3]),
            ],
        )
        all_docs = proc.get_all_documents()
        assert len(all_docs) == 3
        assert all_docs[0].title["en"] == "Proposal"
        assert all_docs[2].title["en"] == "Amendment"

    def test_get_all_documents_empty(self):
        proc = Procedure()
        assert proc.get_all_documents() == []

    def test_start_event_earliest_by_date(self):
        proc = Procedure(events=[
            Event(date="2024-06-01", type="vote"),
            Event(date="2024-01-01", type="proposal"),
            Event(date="2024-03-01", type="committee"),
        ])
        assert proc.start_event.type == "proposal"
        assert proc.start_date == "2024-01-01"

    def test_start_event_empty(self):
        proc = Procedure()
        assert proc.start_event is None
        assert proc.start_date is None

    def test_start_event_no_dates(self):
        proc = Procedure(events=[Event(type="something")])
        assert proc.start_event is None

    def test_adoption_event_base_returns_none(self):
        proc = Procedure(events=[Event(date="2024-01-01")])
        assert proc.adoption_event is None
        assert proc.adoption_date is None

    def test_status_base_defaults(self):
        assert Procedure().status is None
        assert Procedure(events=[Event(date="2024-01-01")]).status == "ongoing"

    def test_init_subclass_warns_on_missing_overrides(self):
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class BareSubclass(Procedure):
                pass

            msgs = [str(x.message) for x in w]
            assert any("adoption_event" in m for m in msgs)
            assert any("status" in m for m in msgs)

    def test_extra_fields(self):
        proc = Procedure(
            title=MultiLangText({"en": "Test"}),
            procedure_type="OLP",
            subject_matters=["trade"],
        )
        assert proc.procedure_type == "OLP"
        assert proc.subject_matters == ["trade"]

    def test_full_roundtrip(self):
        ids = Identifiers()
        ids.add("celex", "52019PC0089")
        ids.add("procedure_ref", "2019/0089/COD")

        proc = Procedure(
            identifiers=ids,
            title=MultiLangText({"en": "Test procedure", "fr": "Procedure test"}),
            procedure_type="OLP",
            events=[
                Event(
                    date="2019-03-01",
                    type="proposal",
                    documents=[Document(title=MultiLangText({"en": "COM doc"}))],
                )
            ],
        )

        data = proc.model_dump()
        assert data["title"] == {"en": "Test procedure", "fr": "Procedure test"}
        assert data["identifiers"] == [
            {"scheme": "celex", "value": "52019PC0089"},
            {"scheme": "procedure_ref", "value": "2019/0089/COD"},
        ]
        assert data["procedure_type"] == "OLP"
        assert data["events"][0]["type"] == "proposal"
        assert "_raw" not in data

        proc2 = Procedure.model_validate(data)
        assert proc2.identifiers.get("celex") == "52019PC0089"
        assert str(proc2.title) == "Test procedure"
        assert proc2.procedure_type == "OLP"

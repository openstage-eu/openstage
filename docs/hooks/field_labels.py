"""mkdocs hook: add origin/type labels and provenance to model member headings.

Inspects actual Python model classes at build time to:
- Label each member's origin: base, overridden, or case-specific
- Label each member's kind: field (data), property (computed), or method
- Add provenance notes for fields with x_source metadata
- Inject inherited field references with links back to base model docs
"""

from __future__ import annotations

import importlib
import inspect
from typing import Any

from bs4 import BeautifulSoup, NavigableString


# Map: page URL path fragment -> list of (module_path, class_name, case_label)
_MODEL_PAGES: dict[str, list[tuple[str, str, str]]] = {
    "eu-models": [
        ("openstage.models.eu.procedure", "EUProcedure", "EU"),
        ("openstage.models.eu.event", "EUEvent", "EU"),
        ("openstage.models.eu.document", "EUDocument", "EU"),
    ],
}

# Base model page path for linking inherited fields
_BASE_PAGE = "base-models"

# Map base class names to their anchor on base-models page
_BASE_ANCHORS: dict[str, str] = {
    "Entity": "entity",
    "Procedure": "procedure",
    "Event": "event",
    "Document": "document",
}

# CSS for badges and provenance notes
_BADGE_CSS = """
<style>
.field-badge {
    display: inline-block;
    font-size: 0.6em;
    font-weight: 600;
    padding: 0.1em 0.45em;
    margin-left: 0.4em;
    border-radius: 3px;
    vertical-align: middle;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.field-badge-base {
    background: #f0f0f0;
    color: #555;
    border: 1px solid #ccc;
}
.field-badge-overridden {
    background: #fff3e0;
    color: #e65100;
    border: 1px solid #ffcc80;
}
.field-badge-case {
    background: #e3f2fd;
    color: #1565c0;
    border: 1px solid #90caf9;
}
.field-badge-field {
    background: #e8f5e9;
    color: #2e7d32;
    border: 1px solid #a5d6a7;
}
.field-badge-property {
    background: #f3e5f5;
    color: #7b1fa2;
    border: 1px solid #ce93d8;
}
.field-badge-method {
    background: #fafafa;
    color: #666;
    border: 1px solid #ddd;
}
.field-provenance {
    font-size: 0.8em;
    color: #777;
    margin-top: 0.15em;
    margin-bottom: 0.3em;
}
.field-provenance code {
    font-size: 0.95em;
    background: #f5f5f5;
    padding: 0.1em 0.3em;
    border-radius: 2px;
}
.inherited-fields {
    margin: 0.5em 0 1em 0;
    padding: 0.6em 1em;
    background: #fafafa;
    border-left: 3px solid #ddd;
    font-size: 0.9em;
}
.inherited-fields code {
    background: #f0f0f0;
    padding: 0.1em 0.3em;
    border-radius: 2px;
}
</style>
"""


def _classify_members(cls: type) -> dict[str, dict[str, str]]:
    """Classify each rendered member of cls (own and inherited).

    Returns a dict mapping member name to:
        origin: 'base', 'overridden', or 'case'
        kind: 'field', 'property', or 'method'
        source: x_source value if present (for provenance)
    """
    # Collect annotations and properties from base classes
    base_annotations: set[str] = set()
    base_properties: set[str] = set()
    base_methods: set[str] = set()
    for base in cls.__mro__[1:]:
        if base is object:
            continue
        base_annotations.update(getattr(base, "__annotations__", {}).keys())
        for name, val in vars(base).items():
            if isinstance(val, property):
                base_properties.add(name)
            elif callable(val) and not name.startswith("_"):
                base_methods.add(name)

    own_annotations = set(
        cls.__annotations__.keys() if hasattr(cls, "__annotations__") else []
    )

    result: dict[str, dict[str, str]] = {}

    # Fields (from annotations on this class)
    for name in own_annotations:
        if name.startswith("_"):
            continue
        origin = "overridden" if name in base_annotations else "case"
        entry: dict[str, str] = {"origin": origin, "kind": "field"}

        # Read x_source from Pydantic field metadata
        if hasattr(cls, "model_fields") and name in cls.model_fields:
            field_info = cls.model_fields[name]
            extra = field_info.json_schema_extra
            if isinstance(extra, dict) and "x_source" in extra:
                entry["source"] = extra["x_source"]

        result[name] = entry

    # Inherited fields (not re-declared on this class)
    for base in cls.__mro__[1:]:
        if base is object or base.__name__ == "BaseModel":
            continue
        for name in getattr(base, "__annotations__", {}):
            if name.startswith("_") or name in result:
                continue
            entry = {"origin": "base", "kind": "field"}
            # Read x_source from Pydantic field metadata
            if hasattr(cls, "model_fields") and name in cls.model_fields:
                field_info = cls.model_fields[name]
                extra = field_info.json_schema_extra
                if isinstance(extra, dict) and "x_source" in extra:
                    entry["source"] = extra["x_source"]
            result[name] = entry

    # Properties defined on this class
    for name, val in vars(cls).items():
        if name.startswith("_") or name in result:
            continue
        if isinstance(val, property):
            origin = "overridden" if name in base_properties else "case"
            result[name] = {"origin": origin, "kind": "property"}

    # Inherited properties (not overridden on this class)
    for base in cls.__mro__[1:]:
        if base is object or base.__name__ == "BaseModel":
            continue
        for name, val in vars(base).items():
            if name.startswith("_") or name in result:
                continue
            if isinstance(val, property):
                result[name] = {"origin": "base", "kind": "property"}

    # Classmethods and regular methods on this class
    for name, val in vars(cls).items():
        if name.startswith("_") and name != "__init__":
            continue
        if name in result:
            continue
        if isinstance(val, classmethod):
            result[name] = {"origin": "case", "kind": "method"}
        elif callable(val) and not isinstance(val, (property, type)):
            result[name] = {"origin": "case", "kind": "method"}

    # Inherited methods (not overridden on this class)
    for base in cls.__mro__[1:]:
        if base is object or base.__name__ == "BaseModel":
            continue
        for name, val in vars(base).items():
            if name.startswith("_") or name in result:
                continue
            if callable(val) and not isinstance(val, (property, classmethod, type)):
                result[name] = {"origin": "base", "kind": "method"}

    return result


def _get_inherited_fields(cls: type) -> list[tuple[str, str, str]]:
    """Get fields inherited from base classes (not re-declared on cls).

    Returns list of (field_name, base_class_name, anchor) tuples.
    """
    own_annotations = set(
        cls.__annotations__.keys() if hasattr(cls, "__annotations__") else []
    )
    inherited: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    for base in cls.__mro__[1:]:
        if base is object or base.__name__ == "BaseModel":
            continue
        base_name = base.__name__
        anchor = _BASE_ANCHORS.get(base_name, base_name.lower())
        for name in getattr(base, "__annotations__", {}):
            if name.startswith("_"):
                continue
            if name not in own_annotations and name not in seen:
                inherited.append((name, base_name, anchor))
                seen.add(name)

    # Also include non-overridden properties from base
    for base in cls.__mro__[1:]:
        if base is object or base.__name__ == "BaseModel":
            continue
        base_name = base.__name__
        anchor = _BASE_ANCHORS.get(base_name, base_name.lower())
        for name, val in vars(base).items():
            if name.startswith("_"):
                continue
            if isinstance(val, property) and name not in vars(cls) and name not in seen:
                inherited.append((name, base_name, anchor))
                seen.add(name)

    return inherited


def _make_origin_badge(origin: str, case_label: str) -> str:
    if origin == "base":
        return '<span class="field-badge field-badge-base">base</span>'
    elif origin == "overridden":
        return '<span class="field-badge field-badge-overridden">overridden</span>'
    return f'<span class="field-badge field-badge-case">{case_label}</span>'


def _make_kind_badge(kind: str) -> str:
    return f'<span class="field-badge field-badge-{kind}">{kind}</span>'


# Base URL for openbasement documentation
_OPENBASEMENT_DOCS = "https://openstage-eu.github.io/openbasement"


def _make_provenance(source: str) -> str:
    """Render a provenance note from an x_source value.

    Parses 'openbasement:template_name.field_name' format and renders
    a linked reference to the openbasement template documentation.
    """
    if source.startswith("openbasement:"):
        ref = source[len("openbasement:"):]
        if "." in ref:
            template, field = ref.split(".", 1)
            return (
                f'<div class="field-provenance">'
                f'Source: <a href="{_OPENBASEMENT_DOCS}/templates/#{template}">'
                f'openbasement</a> template '
                f'<code>{template}</code>, field <code>{field}</code>'
                f'</div>'
            )
    # Fallback for non-openbasement sources
    return (
        f'<div class="field-provenance">'
        f'Source: <code>{source}</code>'
        f'</div>'
    )


def _make_inherited_section(
    inherited: list[tuple[str, str, str]], base_page: str
) -> str:
    """Generate HTML for inherited fields section."""
    if not inherited:
        return ""

    # Group by base class
    by_base: dict[str, list[tuple[str, str]]] = {}
    for name, base_name, anchor in inherited:
        by_base.setdefault(base_name, []).append((name, anchor))

    parts = []
    for base_name, fields in by_base.items():
        anchor = fields[0][1]
        field_links = ", ".join(
            f'<code>{name}</code>' for name, _ in fields
        )
        parts.append(
            f'Inherits from <a href="../{base_page}/#{anchor}">{base_name}</a>: '
            f'{field_links}'
        )

    return (
        f'<div class="inherited-fields">'
        f'{"<br>".join(parts)}'
        f'</div>'
    )


def _strip_details_docstrings(soup: BeautifulSoup) -> bool:
    """Remove repeated class docstrings and field summary lists from Details sections.

    When a class has an Overview block (with docstring) and a Details block
    (with members), the Details block repeats the class docstring and a
    "Fields:" summary list. Both are already shown in the Overview, so this
    function strips them from the Details block.
    """
    modified = False
    for heading in soup.find_all(["h3", "h4"]):
        text = heading.get_text(strip=True)
        if text not in ("Details", "Fields", "Fields and properties"):
            continue
        # Find the next doc-object div (the mkdocstrings class block)
        doc_obj = heading.find_next("div", class_="doc-object")
        if not doc_obj:
            continue
        # The class-level doc-contents div is the first one
        doc_contents = doc_obj.find("div", class_="doc-contents", recursive=False)
        if not doc_contents:
            # Try inside nested structure
            doc_contents = doc_obj.find("div", class_="doc-contents")
        if not doc_contents:
            continue
        # Remove class docstring content and "Fields:" summary list.
        # Stop only at doc-children div (actual member listings) or headings.
        for child in list(doc_contents.children):
            if isinstance(child, NavigableString):
                continue
            tag = child.name if hasattr(child, "name") else None
            # Stop at member container or heading
            if tag in ("h4", "h5"):
                break
            if tag == "div" and "doc" in (child.get("class") or []):
                break
            # Remove class-level docstring paragraphs and code blocks
            if tag in ("p", "div"):
                child.decompose()
                modified = True
            # Remove "Fields:" summary list (already shown in Overview)
            elif tag in ("ul", "ol"):
                child.decompose()
                modified = True
    return modified


def on_page_content(html: str, page: Any, **kwargs: Any) -> str:
    """Post-process page HTML to add field labels, provenance, and inherited refs."""
    # Strip repeated docstrings from any model page with Overview/Details pattern
    is_model_page = any(key in page.url for key in ("base-models", "eu-models"))

    page_key = None
    for key in _MODEL_PAGES:
        if key in page.url:
            page_key = key
            break

    if page_key is None and not is_model_page:
        return html

    soup = BeautifulSoup(html, "html.parser")
    modified = False

    # Strip repeated class docstrings from Details/Fields sections
    if is_model_page:
        if _strip_details_docstrings(soup):
            modified = True

    if page_key is None:
        if modified:
            return str(soup)
        return html

    for module_path, class_name, case_label in _MODEL_PAGES[page_key]:
        try:
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
        except (ImportError, AttributeError):
            continue

        member_map = _classify_members(cls)
        inherited = _get_inherited_fields(cls)

        # Inject inherited fields section after class docstring
        class_id = f"{module_path}.{class_name}"
        class_heading = soup.find(id=class_id)
        if class_heading and inherited:
            # Find the doc-contents div after the class heading
            doc_contents = class_heading.find_next("div", class_="doc-contents")
            if doc_contents:
                inherited_html = _make_inherited_section(inherited, _BASE_PAGE)
                inherited_soup = BeautifulSoup(inherited_html, "html.parser")
                # Insert after the first paragraph (class docstring)
                first_p = doc_contents.find("p")
                if first_p:
                    first_p.insert_after(inherited_soup)
                else:
                    doc_contents.insert(0, inherited_soup)
                modified = True

        # Add badges and provenance to members
        for member_name, info in member_map.items():
            full_id = f"{module_path}.{class_name}.{member_name}"
            heading = soup.find(id=full_id)
            if heading is None:
                continue

            # Add origin badge
            origin_badge = _make_origin_badge(info["origin"], case_label)
            # Add kind badge
            kind_badge = _make_kind_badge(info["kind"])

            badge_html = origin_badge + kind_badge
            badge_soup = BeautifulSoup(badge_html, "html.parser")

            code_el = heading.find("code") or heading.find("span")
            if code_el:
                code_el.append(badge_soup)
                modified = True

            # Add provenance note if x_source present
            if "source" in info:
                prov_html = _make_provenance(info["source"])
                prov_soup = BeautifulSoup(prov_html, "html.parser")
                # Insert provenance after the heading, before doc-contents
                doc_div = heading.find_next("div", class_="doc-contents")
                if doc_div:
                    first_child = doc_div.find()
                    if first_child:
                        first_child.insert_before(prov_soup)
                    else:
                        doc_div.insert(0, prov_soup)
                    modified = True

    if modified:
        css_soup = BeautifulSoup(_BADGE_CSS, "html.parser")
        soup.insert(0, css_soup)
        return str(soup)

    return html

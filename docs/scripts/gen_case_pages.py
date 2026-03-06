"""Generate case model documentation pages from templates and snippets."""

from pathlib import Path

import mkdocs_gen_files

DOCS_DIR = Path("docs")

# -- Shared template pieces (identical for all case pages) --

BADGE_LEGEND = (
    "Members are labelled automatically by origin and kind:\n\n"
    '**Origin:** <span style="display:inline-block;font-size:0.75em;font-weight:600;'
    "padding:0.1em 0.45em;border-radius:3px;background:#f0f0f0;color:#555;"
    'border:1px solid #ccc;text-transform:uppercase;letter-spacing:0.03em">base</span>'
    " inherited from a base model, "
    '<span style="display:inline-block;font-size:0.75em;font-weight:600;'
    "padding:0.1em 0.45em;border-radius:3px;background:#fff3e0;color:#e65100;"
    'border:1px solid #ffcc80;text-transform:uppercase;letter-spacing:0.03em">'
    "overridden</span>"
    " base interface re-implemented with {case} logic, "
    '<span style="display:inline-block;font-size:0.75em;font-weight:600;'
    "padding:0.1em 0.45em;border-radius:3px;background:#e3f2fd;color:#1565c0;"
    'border:1px solid #90caf9;text-transform:uppercase;letter-spacing:0.03em">'
    "{case}</span>"
    " specific to the {case} case.\n\n"
    '**Kind:** <span style="display:inline-block;font-size:0.75em;font-weight:600;'
    "padding:0.1em 0.45em;border-radius:3px;background:#e8f5e9;color:#2e7d32;"
    'border:1px solid #a5d6a7;text-transform:uppercase;letter-spacing:0.03em">'
    "field</span>"
    " data attribute (present in the dataset), "
    '<span style="display:inline-block;font-size:0.75em;font-weight:600;'
    "padding:0.1em 0.45em;border-radius:3px;background:#f3e5f5;color:#7b1fa2;"
    'border:1px solid #ce93d8;text-transform:uppercase;letter-spacing:0.03em">'
    "property</span>"
    " computed value derived from other fields, "
    '<span style="display:inline-block;font-size:0.75em;font-weight:600;'
    "padding:0.1em 0.45em;border-radius:3px;background:#fafafa;color:#666;"
    'border:1px solid #ddd;text-transform:uppercase;letter-spacing:0.03em">'
    "method</span>"
    " programmatic interface."
)

SOFT_VALIDATION_NOTE = (
    "Fields that declare a controlled vocabulary (`x_known_values`) are "
    "soft-validated on construction. Unknown values produce a `UserWarning` "
    "rather than raising an exception, so unexpected data is flagged without "
    "blocking processing."
)

PYDANTIC_FILTERS = [
    "!^model_",
    "!^construct$",
    "!^from_orm$",
    "!^parse_",
    "!^schema",
    "!^update_forward_refs$",
    "!^validate$",
    "!^copy$",
    "!^dict$",
    "!^json$",
]


def read_snippet(case: str, name: str) -> str:
    """Read a markdown snippet file for a case."""
    return (DOCS_DIR / "cases" / case / f"{name}.md").read_text().strip()


def render_class_block(module_path: str) -> str:
    """Render Overview + Details mkdocstrings blocks for one class."""
    filters = "\n".join(f'        - "{f}"' for f in PYDANTIC_FILTERS)
    return f"""### Overview

::: {module_path}
    options:
      members: false

### Details

::: {module_path}
    options:
      show_bases: false
      inherited_members: true
      filters:
{filters}"""


def generate_case_page(config: dict) -> str:
    """Assemble a full case model page."""
    case_id = config["case_id"]
    parts = []

    parts.append(f"# {config['title']}\n")
    parts.append(read_snippet(case_id, "intro"))
    parts.append(BADGE_LEGEND.format(case=config["case_label"]))
    parts.append(SOFT_VALIDATION_NOTE)

    if "provenance" in config.get("snippets", []):
        parts.append(f"## Data provenance\n\n{read_snippet(case_id, 'provenance')}")

    for cls in config["classes"]:
        parts.append(f"## {cls['heading']}\n")
        parts.append(render_class_block(cls["module_path"]))

    if "usage" in config.get("snippets", []):
        parts.append(f"## Usage\n\n{read_snippet(case_id, 'usage')}")

    if "adapter" in config.get("snippets", []):
        parts.append(f"## Adapter\n\n{read_snippet(case_id, 'adapter')}")

    # Codebook section (shared pattern, case-specific import)
    proc = config["classes"][0]
    module = proc["module_path"].rsplit(".", 1)[0]
    parts.append(
        f"## Codebook\n\n"
        f"The field metadata embedded in {config['title'].lower()} can be extracted "
        f"as a codebook. See [Fields and Codebooks](fields-codebook.md) for the full "
        f"documentation.\n\n"
        f"```python\n"
        f"from openstage.models.codebook import extract_codebook, codebook_to_markdown\n"
        f"from {module} import {proc['heading']}\n\n"
        f"entries = extract_codebook({proc['heading']})\n"
        f"print(codebook_to_markdown(entries))\n"
        f"```"
    )

    return "\n\n".join(parts) + "\n"


# -- Case configs --

CASES = [
    {
        "case_id": "eu",
        "case_label": "EU",
        "title": "EU Models",
        "output": "eu-models.md",
        "classes": [
            {
                "heading": "EUProcedure",
                "module_path": "openstage.models.eu.procedure.EUProcedure",
            },
            {
                "heading": "EUEvent",
                "module_path": "openstage.models.eu.event.EUEvent",
            },
            {
                "heading": "EUDocument",
                "module_path": "openstage.models.eu.document.EUDocument",
            },
        ],
        "snippets": ["provenance", "usage", "adapter"],
    },
]

# -- Generate --

for case_config in CASES:
    content = generate_case_page(case_config)
    with mkdocs_gen_files.open(case_config["output"], "w") as f:
        f.write(content)

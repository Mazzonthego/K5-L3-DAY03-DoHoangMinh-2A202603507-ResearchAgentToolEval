
from __future__ import annotations

import re
from typing import Any


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from",
    "are", "was", "were", "has", "have", "had", "but",
    "not", "its", "their", "they", "them", "about",
}

def _terms(text: str) -> set[str]:
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return {word for word in words if word not in STOPWORDS}

def compare_sources(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    items = items or []

    if len(items) < 2:
        return {
            "tool": "compare_sources",
            "error": "At least 2 sources are required."
        }

    source_terms = []
    for item in items:
        text = item.get("summary") or item.get("title") or ""
        source_terms.append(_terms(text))

    common_terms = set.intersection(*source_terms)
    sections = ["# Source Comparison", ""]

    sections += ["## Common Topics"]
    sections.append(
        ", ".join(sorted(common_terms)[:15]) or "No common keywords found."
    )
    sections.append("")

    sections.append("## Individual Sources")
    for index, item in enumerate(items):
        title = item.get("title") or f"Source {index + 1}"
        summary = item.get("summary") or "No summary available."
        unique_terms = source_terms[index] - common_terms

        sections += [
            f"### {index + 1}. {title}",
            summary,
            f"**Distinct keywords:** {', '.join(sorted(unique_terms)[:10]) or 'None'}",
            ""
        ]
    markdown = "\n".join(sections)

    return {
        "tool": "compare_sources",
        "markdown": markdown,
        "source_count": len(items),
        "common_terms": sorted(common_terms)
    }

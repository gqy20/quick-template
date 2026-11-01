#!/usr/bin/env python3
"""Validate the static GitHub Pages artifact without third-party dependencies."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.fragment_links: list[str] = []
        self.local_assets: list[str] = []
        self.errors: list[str] = []
        self.h1_count = 0
        self.main_count = 0
        self.nav_count = 0
        self.title_count = 0
        self.has_description = False
        self.has_viewport = False
        self.has_language = False
        self._in_title = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.append(element_id)

        if tag == "html":
            self.has_language = bool(values.get("lang"))
        elif tag == "title":
            self._in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            self.main_count += 1
        elif tag == "nav":
            self.nav_count += 1
        elif tag == "meta":
            self.has_description |= values.get("name") == "description" and bool(
                values.get("content")
            )
            self.has_viewport |= values.get("name") == "viewport" and bool(values.get("content"))
        elif tag == "button" and values.get("type") is None:
            self.errors.append("Every button must declare its type")
        elif tag == "img" and values.get("alt") is None:
            self.errors.append("Every image must declare alt text")

        if tag == "a":
            href = values.get("href")
            if not href:
                self.errors.append("Every link must have a non-empty href")
            elif href.startswith("#"):
                self.fragment_links.append(href[1:])
            if values.get("target") == "_blank":
                rel = set((values.get("rel") or "").split())
                if not {"noopener", "noreferrer"}.issubset(rel):
                    self.errors.append(
                        f"External new-window link lacks noopener/noreferrer: {href}"
                    )

        for attribute in ("href", "src"):
            value = values.get(attribute)
            if value and self._is_local_asset(value):
                self.local_assets.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title and data.strip():
            self.title_count += 1

    @staticmethod
    def _is_local_asset(value: str) -> bool:
        parsed = urlsplit(value)
        return not parsed.scheme and not parsed.netloc and not value.startswith("#")


def validate_pages(root: Path) -> list[str]:
    index = root / "index.html"
    if not index.is_file():
        return [f"Missing Pages entry: {index}"]

    html = index.read_text(encoding="utf-8")
    errors: list[str] = []
    for marker in ("{{", "}}", "{%", "%}", "{{#"):
        if marker in html:
            errors.append(f"Rendered page contains template marker: {marker}")

    parser = PageParser()
    parser.feed(html)
    errors.extend(parser.errors)

    if not parser.has_language:
        errors.append("The html element must declare a language")
    if not parser.has_viewport:
        errors.append("Missing viewport metadata")
    if not parser.has_description:
        errors.append("Missing page description")
    if parser.title_count != 1:
        errors.append(f"Expected one non-empty title, found {parser.title_count}")
    if parser.h1_count != 1:
        errors.append(f"Expected one h1, found {parser.h1_count}")
    if parser.main_count != 1:
        errors.append(f"Expected one main landmark, found {parser.main_count}")
    if parser.nav_count < 1:
        errors.append("Expected at least one nav landmark")

    duplicate_ids = sorted(
        element_id for element_id in set(parser.ids) if parser.ids.count(element_id) > 1
    )
    if duplicate_ids:
        errors.append(f"Duplicate element ids: {duplicate_ids}")

    known_ids = set(parser.ids)
    missing_fragments = sorted(
        fragment for fragment in set(parser.fragment_links) if fragment not in known_ids
    )
    if missing_fragments:
        errors.append(f"Links reference missing fragments: {missing_fragments}")

    for raw_asset in sorted(set(parser.local_assets)):
        asset_path = urlsplit(raw_asset).path
        if asset_path == "":
            continue
        resolved = (root / asset_path).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            errors.append(f"Local asset escapes docs root: {raw_asset}")
            continue
        if not resolved.is_file():
            errors.append(f"Missing local asset: {raw_asset}")

    required_text = (
        "uv tool install git+https://github.com/gqy20/quick-template",
        "AGENTS.md",
        "DESIGN.md",
        "Claude Agent SDK",
        "LangGraph",
    )
    for text in required_text:
        if text not in html:
            errors.append(f"Missing required current capability text: {text}")

    if "<svg" in html:
        errors.append("Inline SVG is not allowed in the Pages entry")
    if " style=" in html:
        errors.append("Static inline styles are not allowed in the Pages entry")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("docs"))
    args = parser.parse_args()
    errors = validate_pages(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Pages validation passed: {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

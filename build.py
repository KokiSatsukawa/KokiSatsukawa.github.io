#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path


def parse_scalar(value: str):
    value = value.strip()
    if value == "null" or value == "~":
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.startswith("\"") and value.endswith("\""):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.isdigit():
        return int(value)
    return value


def next_nonempty(lines: list[str], start: int) -> tuple[int, str] | tuple[None, None]:
    for i in range(start, len(lines)):
        stripped = lines[i].strip()
        if stripped and not stripped.startswith("#"):
            return i, lines[i]
    return None, None


def parse_yaml_like(text: str) -> dict:
    lines = text.splitlines()
    root: dict = {}
    stack: list[tuple[int, object]] = [(-1, root)]

    for idx, raw_line in enumerate(lines):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if line.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"Expected list at line {idx + 1}")
            item_content = line[2:].strip()
            if not item_content:
                item: dict = {}
                parent.append(item)
                stack.append((indent, item))
                continue
            if ":" in item_content:
                key, value = item_content.split(":", 1)
                key = key.strip()
                value = value.strip()
                item: dict = {}
                if value == "":
                    next_idx, next_line = next_nonempty(lines, idx + 1)
                    if next_line is None:
                        item[key] = {}
                    else:
                        next_indent = len(next_line) - len(next_line.lstrip(" "))
                        next_stripped = next_line.strip()
                        if next_indent > indent and next_stripped.startswith("- "):
                            item[key] = []
                        else:
                            item[key] = {}
                    parent.append(item)
                    stack.append((indent, item[key]))
                else:
                    item[key] = parse_scalar(value)
                    parent.append(item)
                    next_idx, next_line = next_nonempty(lines, idx + 1)
                    if next_line is not None:
                        next_indent = len(next_line) - len(next_line.lstrip(" "))
                        if next_indent > indent:
                            stack.append((indent, item))
                continue
            parent.append(parse_scalar(item_content))
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                next_idx, next_line = next_nonempty(lines, idx + 1)
                if next_line is None:
                    container: object = {}
                else:
                    next_indent = len(next_line) - len(next_line.lstrip(" "))
                    next_stripped = next_line.strip()
                    if next_indent > indent and next_stripped.startswith("- "):
                        container = []
                    else:
                        container = {}
                if isinstance(parent, dict):
                    parent[key] = container
                else:
                    raise ValueError(f"Unexpected container parent at line {idx + 1}")
                stack.append((indent, container))
            else:
                if isinstance(parent, dict):
                    parent[key] = parse_scalar(value)
                else:
                    raise ValueError(f"Unexpected scalar parent at line {idx + 1}")
            continue
        raise ValueError(f"Unrecognized line at {idx + 1}: {line}")

    return root


def load_source(path: Path) -> dict:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    text = path.read_text(encoding="utf-8")
    return parse_yaml_like(text)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    result = text
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def build_json(data: dict) -> dict:
    return {
        "web": data.get("web", {}),
        "publications": data.get("publications", []),
    }


def build_latex(data: dict, output_path: Path) -> None:
    publications = data.get("publications", [])
    sections: "OrderedDict[str, list[dict]]" = OrderedDict()
    for entry in publications:
        subtype = entry.get("subtype", "uncategorized")
        sections.setdefault(subtype, []).append(entry)

    subtype_labels = data.get("web", {}).get("subtype_labels", {})

    lines = ["% Auto-generated from data/cv_source.yaml", ""]
    for subtype, items in sections.items():
        label = subtype_labels.get(subtype, subtype.replace("_", " ").title())
        lines.append(f"\\section*{{{latex_escape(label)}}}")
        lines.append("\\begin{enumerate}")
        for entry in items:
            title = latex_escape(entry.get("title", ""))
            authors = latex_escape(entry.get("authors", ""))
            venue = latex_escape(entry.get("venue", ""))
            year = entry.get("year")
            year_text = latex_escape(str(year)) if year else ""
            links = entry.get("links", []) or []
            link_text = ""
            if links:
                first = links[0]
                url = latex_escape(first.get("url", ""))
                label = latex_escape(first.get("label", "Link"))
                if url:
                    link_text = f" \\href{{{url}}}{{{label}}}"
            parts = [part for part in [title, authors, venue, year_text] if part]
            body = ". ".join(parts)
            lines.append(f"\\item {body}.{link_text}")
        lines.append("\\end{enumerate}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def build_bib(data: dict, output_path: Path) -> None:
    publications = data.get("publications", [])
    entries = []
    for entry in publications:
        entry_id = entry.get("id", "untitled")
        title = entry.get("title", "")
        authors = entry.get("authors", "")
        year = entry.get("year")
        venue = entry.get("venue", "")
        links = entry.get("links", []) or []
        url = links[0].get("url") if links else ""
        fields = [
            f"  title = {{{title}}}",
            f"  author = {{{authors}}}",
        ]
        if year:
            fields.append(f"  year = {{{year}}}")
        if venue:
            fields.append(f"  note = {{{venue}}}")
        if url:
            fields.append(f"  howpublished = {{{url}}}")
        entries.append("@misc{%s,\n%s\n}" % (entry_id, ",\n".join(fields)))
    output_path.write_text("\n\n".join(entries) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CV outputs from YAML source.")
    parser.add_argument("--source", default="data/cv_source.yaml", help="Path to YAML source")
    parser.add_argument("--output", default="output", help="Output directory")
    args = parser.parse_args()

    source_path = Path(args.source)
    output_dir = Path(args.output)
    data = load_source(source_path)

    ensure_dir(output_dir)
    ensure_dir(output_dir / "latex")

    json_payload = build_json(data)
    (output_dir / "cv.json").write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    build_latex(data, output_dir / "latex" / "publications.tex")
    build_bib(data, output_dir / "publications.bib")


if __name__ == "__main__":
    main()

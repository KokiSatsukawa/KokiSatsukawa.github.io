#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys


def load_yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required to build cv.json. "
            "Install it with: python -m pip install pyyaml"
        ) from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise SystemExit("cv_source.yaml must contain a YAML mapping at the top level.")

    return data


def build_json(data: dict) -> dict:
    publications = data.get("publications", [])
    web_publications = [
        normalize_publication(publication, variant="web")
        for publication in publications
        if publication.get("web", True)
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "meta": data.get("meta", {}),
        "web": data.get("web", {}),
        "publications": web_publications,
        "grants": data.get("grants", []),
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_bibtex(output_dir: Path, publications: list[dict]) -> None:
    entries = [pub["bibtex"].strip() for pub in publications if pub.get("bibtex")]
    if not entries:
        return

    bib_path = output_dir / "publications.bib"
    bib_path.write_text("\n\n".join(entries) + "\n", encoding="utf-8")


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
    return "".join(replacements.get(char, char) for char in text)


def normalize_publication(publication: dict, variant: str) -> dict:
    title = publication.get(f"title_{variant}") or publication.get("title", "")
    venue = publication.get(f"venue_{variant}") or publication.get("venue", "")
    normalized = {
        "id": publication.get("id"),
        "subtype": publication.get("subtype"),
        "title": title,
        "authors": publication.get("authors", ""),
        "venue": venue,
        "venue_link": publication.get("venue_link"),
        "year": publication.get("year"),
        "link": publication.get("link"),
        "doi": publication.get("doi"),
    }
    return {key: value for key, value in normalized.items() if value}


def format_publication(pub: dict) -> str:
    title = latex_escape(pub.get("title_pdf") or pub.get("title", ""))
    authors = latex_escape(pub.get("authors", ""))
    venue = latex_escape(pub.get("venue_pdf") or pub.get("venue", ""))
    year = pub.get("year")
    link = pub.get("link") or pub.get("doi")
    if link:
        title = rf"\href{{{link}}}{{{title}}}"
    parts = [part for part in [title, authors, venue] if part]
    if year:
        parts.append(f"({year})")
    return r"\item " + " ".join(parts)


def format_grant(grant: dict) -> str:
    title = latex_escape(grant.get("title", ""))
    agency = latex_escape(grant.get("agency", ""))
    role = latex_escape(grant.get("role", ""))
    period = latex_escape(grant.get("period", ""))
    amount = latex_escape(grant.get("amount", ""))
    parts = [part for part in [title, agency, role, period, amount] if part]
    return r"\item " + r" \textbullet{} ".join(parts)


def write_tex_sections(output_dir: Path, data: dict) -> None:
    sections_dir = output_dir / "sections"
    sections_dir.mkdir(exist_ok=True)

    publications = data.get("publications", [])
    publications_tex = "\n".join(format_publication(pub) for pub in publications)
    publications_body = "\n".join(
        [
            r"\begin{enumerate}",
            publications_tex,
            r"\end{enumerate}",
            "",
        ]
    )
    (sections_dir / "publications.tex").write_text(publications_body, encoding="utf-8")

    grants = data.get("grants", [])
    grants_tex = "\n".join(format_grant(grant) for grant in grants)
    grants_body = "\n".join(
        [
            r"\begin{itemize}",
            grants_tex,
            r"\end{itemize}",
            "",
        ]
    )
    (sections_dir / "grants.tex").write_text(grants_body, encoding="utf-8")

    complete_cv = "\n".join(
        [
            r"\documentclass{article}",
            r"\usepackage[hidelinks]{hyperref}",
            r"\usepackage[margin=1in]{geometry}",
            r"\begin{document}",
            r"\section*{Publications}",
            r"\input{sections/publications}",
            r"\section*{Grants}",
            r"\input{sections/grants}",
            r"\end{document}",
            "",
        ]
    )
    (output_dir / "complete_cv.tex").write_text(complete_cv, encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parent
    source_path = root / "data" / "cv_source.yaml"
    if not source_path.exists():
        print(f"Missing source file: {source_path}", file=sys.stderr)
        return 1

    data = load_yaml(source_path)
    output_dir = root / "output"
    output_dir.mkdir(exist_ok=True)

    payload = build_json(data)
    write_json(output_dir / "cv.json", payload)
    write_bibtex(output_dir, data.get("publications", []))
    write_tex_sections(output_dir, data)

    print(f"Wrote {output_dir / 'cv.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
    venue_raw = pub.get("venue_pdf") or pub.get("venue", "")
    year = pub.get("year")
    month = pub.get("month")
    subtype = pub.get("subtype", "")

    venue_parts = [part.strip() for part in str(venue_raw).split(",") if part.strip()]
    venue_name = latex_escape(venue_parts[0]) if venue_parts else ""
    venue_rest = ", ".join(latex_escape(part) for part in venue_parts[1:])

    if subtype == "international_conference_peer_reviewed":
        location = venue_rest
        date_parts = []
        if month:
            date_parts.append(latex_escape(month))
        if year:
            date_parts.append(str(year))
        date_text = " ".join(date_parts)
        parts = [
            authors,
            title,
            rf"\textit{{{venue_name}}}",
            location,
            date_text,
        ]
    else:
        parts = [
            authors,
            title,
            rf"\textit{{{venue_name}}}",
            venue_rest,
            str(year) if year else "",
        ]

    cleaned = [part for part in parts if part]
    return r"\item " + ", ".join(cleaned) + "."


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
    display_sections = data.get("web", {}).get("display_subtypes", [])
    section_blocks = []
    for section in display_sections:
        items = [pub for pub in publications if pub.get("subtype") == section.get("id")]
        if not items:
            continue
        items_tex = "\n".join(format_publication(pub) for pub in items)
        section_blocks.extend(
            [
                rf"\section{{{latex_escape(section.get('label', ''))}}}",
                r"\begin{enumerate}[label={[\thesection.\arabic*]}]",
                items_tex,
                r"\end{enumerate}",
                "",
            ]
        )
    publications_body = "\n".join(section_blocks)
    (sections_dir / "publications.tex").write_text(publications_body, encoding="utf-8")

    grants = data.get("grants", [])
    grants_tex = "\n".join(format_grant(grant) for grant in grants)
    grants_body = "\n".join(
        [
            r"\section{Grants}",
            r"\begin{enumerate}[label={[\thesection.\arabic*]}]",
            grants_tex,
            r"\end{enumerate}",
            "",
        ]
    )
    (sections_dir / "grants.tex").write_text(grants_body, encoding="utf-8")

    complete_cv = "\n".join(
        [
            r"\documentclass[dvipdfmx,11pt,nomag,a4paper]{jsarticle}",
            "",
            r"%%% ---------- レイアウト ----------",
            r"\usepackage[top=20mm,bottom=20mm,left=22mm,right=22mm]{geometry}",
            "",
            r"%%% ---------- フォント ----------",
            r"\usepackage{newpxtext}",
            r"%\usepackage{newtxtext}",
            "",
            r"%%% ---------- 見出し ----------",
            r"%\usepackage{sectsty}",
            r"%\allsectionsfont{\sffamily\bfseries\Large}",
            "",
            r"%%% ---------- 行間・段落 ----------",
            r"\usepackage{setspace}",
            r"\setstretch{0.95}",
            r"\setlength{\parindent}{0pt}",
            r"\setlength{\parskip}{4pt}",
            "",
            r"%%% ---------- リスト操作 ----------",
            r"\usepackage{enumitem}",
            r"",
            r"\setlist[enumerate]{%",
            r"  itemsep=.55\baselineskip,",
            r"  topsep=.4\baselineskip,",
            r"  leftmargin=*",
            r"}",
            "",
            r"%%% ---------- ハイパーリンク ----------",
            r"%\usepackage[dvipdfmx,colorlinks=false,linkcolor=blue,urlcolor=blue]{hyperref}",
            r"%\urlstyle{same}",
            "",
            r"%%% ---------- 個人情報マクロ ----------",
            r"\newcommand{\myName}{佐津川功季}",
            r"\newcommand{\myAffiliation}{金沢大学　融合学域}",
            r"\newcommand{\myTitle}{講師}",
            "",
            r"%%% ---------- タイトル ----------",
            r"\title{\LARGE\bfseries 研究業績リスト / Curriculum Vitae}",
            r"\author{ \myAffiliation ~~ \myTitle  ~~ \myName }",
            r"\date{\today}",
            "",
            r"\begin{document}",
            r"\maketitle",
            r"\input{sections/publications}",
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

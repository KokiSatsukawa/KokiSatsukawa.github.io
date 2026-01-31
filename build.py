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
        "invited_talks": data.get("invited_talks", []),
        "presentations": data.get("presentations", []),
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
    title = (
        publication.get(f"title_{variant}")
        or publication.get("title_web")
        or publication.get("title_pdf")
        or publication.get("title", "")
    )
    authors = (
        publication.get(f"authors_{variant}")
        or publication.get("authors_web")
        or publication.get("authors_pdf")
        or publication.get("authors", "")
    )
    venue = (
        publication.get(f"venue_{variant}")
        or publication.get("venue_web")
        or publication.get("venue_pdf")
        or publication.get("venue", "")
    )
    normalized = {
        "id": publication.get("id"),
        "subtype": publication.get("subtype"),
        "title": title,
        "authors": authors,
        "venue": venue,
        "location": publication.get("location"),
        "venue_link": publication.get("venue_link"),
        "year": publication.get("year"),
        "month": publication.get("month"),
        "status": publication.get("status"),
        "language": publication.get("language"),
        "volume": publication.get("volume"),
        "number": publication.get("number"),
        "pages": publication.get("pages"),
        "link": publication.get("link"),
        "doi": publication.get("doi"),
    }
    return {key: value for key, value in normalized.items() if value}


def format_publication(pub: dict) -> str:
    title = latex_escape(
        pub.get("title_pdf")
        or pub.get("title_web")
        or pub.get("title", "")
    )
    authors = latex_escape(
        pub.get("authors_pdf")
        or pub.get("authors_web")
        or pub.get("authors", "")
    )
    venue_raw = (
        pub.get("venue_pdf")
        or pub.get("venue_web")
        or pub.get("venue", "")
    )
    volume = pub.get("volume")
    number = pub.get("number")
    pages = pub.get("pages")
    year = pub.get("year")
    month = pub.get("month")
    subtype = pub.get("subtype", "")
    accepted = pub.get("status") == "accepted"

    venue_parts = [part.strip() for part in str(venue_raw).split(",") if part.strip()]
    venue_name = latex_escape(venue_raw)
    venue_rest = ""

    volume_text = latex_escape(str(volume)) if volume else ""
    number_text = latex_escape(str(number)) if number else ""
    pages_text = latex_escape(str(pages)) if pages else ""

    extra_text = ""
    if volume_text and number_text:
        extra_text = f"{volume_text}({number_text})"
    elif volume_text:
        extra_text = f"{volume_text}"
    if pages_text:
        extra_text = f"{extra_text}, {pages_text}" if extra_text else f"{pages_text}"
    if extra_text:
        venue_rest = f"{venue_rest}, {extra_text}" if venue_rest else extra_text

    if subtype == "international_conference_peer_reviewed":
        location = latex_escape(pub.get("location") or "")
        if not location and venue_parts:
            venue_name = latex_escape(venue_parts[0])
            location = ", ".join(latex_escape(part) for part in venue_parts[1:])
        date_parts = []
        if month:
            date_parts.append(latex_escape(month))
        if year:
            date_parts.append(str(year))
        date_text = " ".join(date_parts)
        if accepted:
            date_text = f"{date_text} (Accepted)" if date_text else "(Accepted)"
        parts = [
            authors,
            title,
            rf"\textit{{{venue_name}}}",
            location,
            date_text,
        ]
    else:
        venue_name = latex_escape(venue_raw)
        venue_rest = ""
        year_text = ""
        if year:
            year_text = f"{latex_escape(month)} {year}" if month else str(year)
        if accepted:
            year_text = f"{year_text} (Accepted)" if year_text else "(Accepted)"
        parts = [
            authors,
            title,
            rf"\textit{{{venue_name}}}",
            venue_rest,
            year_text,
        ]

    cleaned = [part for part in parts if part]
    return ", ".join(cleaned) + "."


def format_generic_entry(entry: dict, fields: list[str]) -> str:
    values = []
    for field in fields:
        value = entry.get(field)
        if value is None and not field.endswith(("_web", "_pdf")):
            value = entry.get(f"{field}_pdf")
        if value is None and not field.endswith(("_web", "_pdf")):
            value = entry.get(f"{field}_web")
        if value is None and field == "date":
            month = entry.get("month")
            year = entry.get("year")
            if month and year:
                value = f"{month} {year}"
            elif year:
                value = str(year)
        if not value:
            continue
        values.append(latex_escape(str(value)))
    if not values:
        return ""
    return ", ".join(values) + "."


def write_tex_sections(output_dir: Path, data: dict) -> None:
    sections_dir = output_dir / "sections"
    sections_dir.mkdir(exist_ok=True)

    cv_sections = data.get("cv", {}).get("sections", [])
    cv_blocks = []

    for section in cv_sections:
        label = latex_escape(section.get("label", ""))
        source_key = section.get("source", "")
        entries = data.get(source_key, [])
        subtypes = section.get("subtypes")
        if subtypes:
            entries = [entry for entry in entries if entry.get("subtype") in subtypes]

        if not entries and not section.get("subsections"):
            continue

        cv_blocks.append(rf"\section{{{label}}}")
        has_list = False
        subsection_started = False

        def render_entries(items: list[dict], resume: bool, list_mode: bool = True) -> None:
            nonlocal has_list, subsection_started
            if not items:
                return
            if list_mode:
                option = (
                    r"[label={[\thesection.\arabic*]}]"
                    if not resume
                    else r"[resume,label={[\thesection.\arabic*]}]"
                )
                cv_blocks.append(rf"\begin{{enumerate}}{option}")
            for entry in items:
                fmt = section.get("format")
                if fmt == "publication":
                    text = format_publication(entry)
                else:
                    fields = section.get("fields", [])
                    text = format_generic_entry(entry, fields)
                if text:
                    if list_mode:
                        cv_blocks.append(rf"\item {text}")
                    else:
                        cv_blocks.append(rf"\noindent {text}\\")
            if list_mode:
                cv_blocks.append(r"\end{enumerate}")
                has_list = True
                subsection_started = True

        subsections = section.get("subsections") or []
        if subsections:
            resume = False
            for subsection in subsections:
                sub_label = latex_escape(subsection.get("label", ""))
                cv_blocks.append(rf"\subsection*{{{sub_label}}}")
                subtypes = subsection.get("subtypes", [])
                items = [entry for entry in entries if entry.get("subtype") in subtypes]
                list_mode = subsection.get("list", True)
                render_entries(items, resume=resume, list_mode=list_mode)
                if items and list_mode:
                    resume = True
            if not has_list:
                cv_blocks.append(r"\begin{enumerate}[label={[\thesection.\arabic*]}]")
                cv_blocks.append(r"\end{enumerate}")
        else:
            render_entries(entries, resume=False)

        cv_blocks.append("")

    cv_body = "\n".join(cv_blocks)
    (sections_dir / "cv.tex").write_text(cv_body, encoding="utf-8")

    complete_cv = "\n".join(
        [
            r"\documentclass[dvipdfmx,11pt,nomag,a4paper]{jsarticle}",
            "",
            r"%%% ---------- レイアウト ----------",
            r"\usepackage[top=20mm,bottom=20mm,left=22mm,right=22mm]{geometry}",
            "",
            r"%%% ---------- フォント ----------",
            r"%\usepackage{newpxtext}",
            r"\usepackage{newtxtext}",
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
            r"\input{sections/cv}",
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

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
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "meta": data.get("meta", {}),
        "web": data.get("web", {}),
        "publications": data.get("publications", []),
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

    print(f"Wrote {output_dir / 'cv.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

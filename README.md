# KokiSatsukawa.github.io

## Publications workflow (single source)

This site uses a single YAML source of truth for publications and generates the JSON that the Publications page renders.

### Files
- `data/cv_source.yaml`: Source data for publications and web display settings.
- `build.py`: Generates `output/cv.json` (and optional `output/publications.bib` if `bibtex` fields are present).
- `output/cv.json`: Generated JSON consumed by `Publications.html`.

### Update steps
1. Edit `data/cv_source.yaml`.
2. Generate the web JSON:
   ```bash
   python -m pip install pyyaml
   python build.py
   ```
3. (Optional) Generate the complete PDF CV from your LaTeX workflow and place it at the path in `meta.complete_pdf_url` (currently `images/List.pdf`).
4. Commit changes and push to GitHub.

### Local preview
Because the Publications page fetches `output/cv.json`, local `file://` access may fail. Use a local server such as **VS Code Live Server** to preview the site.

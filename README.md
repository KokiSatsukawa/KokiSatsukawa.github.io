# KokiSatsukawa.github.io

## Publications workflow (single source)

This site uses a single YAML source of truth for publications and generates the JSON that the Publications page renders, along with LaTeX section files for the complete PDF.

### Files
- `data/cv_source.yaml`: Source data for publications, grants (PDF-only), and web display settings. Use `title_web`/`authors_web`/`venue_web` for website text and `title_pdf`/`authors_pdf`/`venue_pdf` for the PDF, and define CV sections under `cv.sections`.
- `build.py`: Generates `output/cv.json`, LaTeX section files in `output/sections/`, and optional `output/publications.bib` if `bibtex` fields are present.
- `output/cv.json`: Generated JSON consumed by `Publications.html`.
- `output/sections/cv.tex`: LaTeX CV sections assembled from `cv.sections`.
- `output/complete_cv.tex`: Minimal LaTeX wrapper that inputs the generated CV sections.

### Update steps
1. Edit `data/cv_source.yaml`.
2. Generate the web JSON and LaTeX section files:
   ```bash
   python -m pip install pyyaml
   python build.py
   ```
3. (Optional) In your LaTeX CV, include the generated section file:
   ```tex
   \input{output/sections/cv}
   ```
   Then generate the complete PDF CV and place it at the path in `meta.complete_pdf_url` (currently `output/complete_cv.pdf`).
4. Commit changes and push to GitHub.

### Local preview
Because the Publications page fetches `output/cv.json`, local `file://` access may fail. Use a local server such as **VS Code Live Server** to preview the site.

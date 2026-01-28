# KokiSatsukawa.github.io

## Publications data workflow

This repository keeps a single source of truth for publications and generates both web and PDF-friendly outputs.

### Source data

* Edit `data/cv_source.yaml`.
* The file contains all publications with a `subtype` field. The website filters to the subtypes listed in
  `web.display_subtypes`, so you can add new types later without changing the JavaScript.

### Build outputs

Run the build script from the repository root:

```sh
python3 build.py
```

This generates:

* `output/cv.json` (used by `Publications.html`).
* `output/latex/publications.tex` and `output/publications.bib` (inputs for the complete PDF).

Commit `output/cv.json` so GitHub Pages can serve the data.

### PDF (complete list)

1. Place the generated PDF at `assets/cv.pdf` (or update `web.pdf_link` in `data/cv_source.yaml`).
2. Use `output/latex/publications.tex` and/or `output/publications.bib` in your LaTeX build as needed.

### Local preview

Because browsers block `fetch()` on `file://` URLs, preview the site using a local server.
For example, with VS Code Live Server:

* Right-click `Publications.html` and choose **Open with Live Server**.


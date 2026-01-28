(function () {
  const dataUrl = "output/cv.json";
  const root = document.getElementById("publications-root");
  const status = document.getElementById("publications-status");
  const pdfLink = document.getElementById("publications-pdf-link");

  if (!root) {
    return;
  }

  function formatLabel(label) {
    return label
      .split("_")
      .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
      .join(" ");
  }

  function renderEntry(entry) {
    const item = document.createElement("li");
    item.className = "publication-item";

    const title = document.createElement("div");
    title.className = "publication-title";
    title.textContent = entry.title || "Untitled";

    const authors = document.createElement("div");
    authors.className = "publication-authors";
    authors.textContent = entry.authors || "";

    const venue = document.createElement("div");
    venue.className = "publication-venue";
    const pieces = [];
    if (entry.venue) {
      pieces.push(entry.venue);
    }
    if (entry.year) {
      pieces.push(entry.year);
    }
    venue.textContent = pieces.join(" • ");

    item.appendChild(title);
    if (entry.authors) {
      item.appendChild(authors);
    }
    if (pieces.length) {
      item.appendChild(venue);
    }

    if (Array.isArray(entry.links) && entry.links.length) {
      const links = document.createElement("div");
      links.className = "publication-links";
      entry.links.forEach((link, index) => {
        if (!link.url) {
          return;
        }
        const anchor = document.createElement("a");
        anchor.href = link.url;
        anchor.target = "_blank";
        anchor.rel = "noopener noreferrer";
        anchor.textContent = link.label || "Link";
        links.appendChild(anchor);
        if (index < entry.links.length - 1) {
          links.appendChild(document.createTextNode(" • "));
        }
      });
      item.appendChild(links);
    }

    return item;
  }

  function renderSection(label, entries) {
    const section = document.createElement("section");
    section.className = "publications-section";

    const heading = document.createElement("h3");
    heading.className = "section-title";
    heading.textContent = label;
    section.appendChild(heading);

    if (!entries.length) {
      const empty = document.createElement("p");
      empty.className = "detail-text";
      empty.textContent = "No entries yet.";
      section.appendChild(empty);
      return section;
    }

    const list = document.createElement("ol");
    list.className = "LICV publications-list";
    entries.forEach((entry) => {
      list.appendChild(renderEntry(entry));
    });
    section.appendChild(list);
    return section;
  }

  fetch(dataUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to load publications data.");
      }
      return response.json();
    })
    .then((data) => {
      const publications = data.publications || [];
      const web = data.web || {};
      const displaySubtypes = web.display_subtypes || [];
      const labels = web.subtype_labels || {};

      if (pdfLink && web.pdf_link) {
        pdfLink.href = web.pdf_link;
      }

      root.innerHTML = "";
      displaySubtypes.forEach((subtype) => {
        const entries = publications.filter((entry) => entry.subtype === subtype);
        const label = labels[subtype] || formatLabel(subtype);
        root.appendChild(renderSection(label, entries));
      });

      if (status) {
        status.textContent = "";
      }
    })
    .catch((error) => {
      if (status) {
        status.textContent =
          "Unable to load publications data. Run this page via a local server (e.g., VS Code Live Server) to allow fetch().";
      }
      console.error(error);
    });
})();

"""Uniformiza categorias exibidas, sem mudar arquivos, URLs ou o texto literario."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / "_site"
ALIASES = {"Projeto": "Projetos", "Tese": "Ensaios"}
HISTORICAL_PATHS = {"projeto": "Projetos", "tese": "Ensaios"}


def display(value: str) -> str:
    return ALIASES.get(value.strip(), value.strip())


def normalize_page(path: Path) -> bool:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    changed = False

    # Metadados de artigos e resumos; nunca substitui palavras no corpo da obra.
    for element in soup.select(".post-context, .post-card .meta"):
        previous = element.get_text(" ", strip=True)
        updated = previous
        for old, new in ALIASES.items():
            if previous.startswith(old + " ·"):
                updated = new + previous[len(old):]
            elif previous.endswith(" — " + old):
                updated = previous[:-len(old)] + new
        if updated != previous:
            element.string = updated
            changed = True

    for element in soup.select(".posted a:not(.tag), .post-navigation .category a"):
        label = element.get_text(" ", strip=True)
        replacement = display(label)
        if replacement != label:
            element.string = replacement
            changed = True

    for element in soup.select(".archive-list .small"):
        label = element.get_text(" ", strip=True)
        if label in {"[Projeto]", "[Tese]"}:
            element.string = "[" + display(label[1:-1]) + "]"
            changed = True

    for element in soup.select(".rightbar a"):
        href = element.get("href", "")
        for directory, new_label in HISTORICAL_PATHS.items():
            if href.endswith("/" + directory + "/index.html") or href == directory + "/index.html":
                if element.get_text(" ", strip=True) in ALIASES:
                    element.string = new_label
                    changed = True

    if changed:
        path.write_text(str(soup), encoding="utf-8")
    return changed


def main() -> int:
    pages = sorted(ROOT.rglob("*.html"))
    changed = sum(normalize_page(path) for path in pages)
    print(f"Categorias normalizadas em {changed} de {len(pages)} paginas HTML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

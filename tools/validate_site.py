from __future__ import annotations
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / "_site"
ATTRS = (("a", "href"), ("img", "src"), ("link", "href"), ("script", "src"))


def is_external(v: str) -> bool:
    s = urlsplit(v)
    return bool(s.scheme or s.netloc) or v.startswith(("mailto:", "tel:", "javascript:", "data:"))


def main() -> int:
    missing = []
    checked = 0
    html_files = list(ROOT.rglob("*.html"))
    for page in html_files:
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        for tag, attr in ATTRS:
            for el in soup.find_all(tag):
                value = el.get(attr)
                if not value or value.startswith("#") or is_external(value):
                    continue
                pathpart = unquote(urlsplit(value).path)
                if not pathpart:
                    continue
                target = (ROOT / pathpart.lstrip("/")) if pathpart.startswith("/") else (page.parent / pathpart)
                target = target.resolve()
                if target.is_dir(): target = target / "index.html"
                checked += 1
                if not target.exists():
                    missing.append((page.relative_to(ROOT).as_posix(), value))
    print(f"Páginas HTML: {len(html_files)}")
    print(f"Referências locais verificadas: {checked}")
    print(f"Ausências: {len(missing)}")
    for page, value in missing[:50]: print(f"  {page} -> {value}")
    return 1 if missing else 0

if __name__ == "__main__":
    raise SystemExit(main())

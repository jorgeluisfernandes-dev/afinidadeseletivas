from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
BEACON_URL = "https://static.cloudflareinsights.com/beacon.min.js"
SITE_TOKEN = "22454232509144f3bb327ecb38fd03ff"
SNIPPET = (
    "<!-- Cloudflare Web Analytics -->"
    "<script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' "
    f"data-cf-beacon='{{\"token\": \"{SITE_TOKEN}\"}}'></script>"
    "<!-- End Cloudflare Web Analytics -->"
)


def main() -> int:
    if not SITE.exists():
        raise SystemExit("ERRO: _site não existe. Execute tools/build_site.py primeiro.")

    inserted = 0
    already_present = 0
    without_body = []

    for path in sorted(SITE.rglob("*.html")):
        text = path.read_text(encoding="utf-8")

        if BEACON_URL in text:
            already_present += 1
            continue

        if not re.search(r"</body\s*>", text, flags=re.IGNORECASE):
            without_body.append(path.relative_to(SITE).as_posix())
            continue

        updated = re.sub(
            r"</body\s*>",
            f"\n{SNIPPET}\n</body>",
            text,
            count=1,
            flags=re.IGNORECASE,
        )
        path.write_text(updated, encoding="utf-8")
        inserted += 1

    print(f"Cloudflare Web Analytics inserido em {inserted} páginas HTML.")
    if already_present:
        print(f"Beacon já presente em {already_present} páginas; nenhuma duplicação foi feita.")
    if without_body:
        print(f"Aviso: {len(without_body)} páginas sem </body> não receberam o beacon.")
        for rel in without_body[:20]:
            print(f"  - {rel}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

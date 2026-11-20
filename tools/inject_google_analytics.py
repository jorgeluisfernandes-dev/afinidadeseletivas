"""Instala GA4 nas paginas geradas sem alterar o acervo-fonte.

O ID de medicao e publico (nao e uma chave de API). O painel de relatorios
permanece privado na conta Google Analytics do proprietario.
"""
from __future__ import annotations

import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "_site"
MEASUREMENT_ID = "G-RPTB8H6JGP"
GTAG_URL = "https://www.googletagmanager.com/gtag/js"
SNIPPET = f"""<!-- Google Analytics 4 -->
<script async src="{GTAG_URL}?id={MEASUREMENT_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{MEASUREMENT_ID}');
</script>
<!-- Fim Google Analytics 4 -->"""


def main() -> int:
    if not SITE.is_dir():
        raise SystemExit("ERRO: monte _site antes de instalar o Analytics.")

    inserted = 0
    present = 0
    skipped = []
    for path in sorted(SITE.rglob("*.html")):
        html = path.read_text(encoding="utf-8")
        head = re.search(r"<head\b[^>]*>", html, flags=re.IGNORECASE)
        if not head and not re.search(r"</body\s*>", html, flags=re.IGNORECASE):
            # Arquivos simples de verificacao de dominio, sem documento HTML.
            skipped.append(path.relative_to(SITE).as_posix())
            continue
        if not head:
            raise RuntimeError(f"Pagina HTML sem <head>: {path}")
        if GTAG_URL in html:
            if (f"{GTAG_URL}?id={MEASUREMENT_ID}" in html
                    and html.count(GTAG_URL) == 1
                    and html.count(f"gtag('config', '{MEASUREMENT_ID}')") == 1):
                present += 1
                continue
            raise RuntimeError(f"Tag Google preexistente ou duplicada: {path}")

        updated = html[:head.end()] + "\n" + SNIPPET + "\n" + html[head.end():]
        path.write_text(updated, encoding="utf-8")
        inserted += 1

    print(f"Google Analytics GA4 {MEASUREMENT_ID}: {inserted} paginas instrumentadas.")
    if present:
        print(f"Configuracao ja presente em {present} paginas, sem duplicacao.")
    if skipped:
        print(f"Arquivos de verificacao sem HTML (ignorados): {len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

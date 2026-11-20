"""Confere se Cloudflare e Google Analytics estao instalados uma vez por pagina."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "_site"
BEACON = "https://static.cloudflareinsights.com/beacon.min.js"
GOOGLE = "https://www.googletagmanager.com/gtag/js?id=G-RPTB8H6JGP"
GA_CONFIG = "gtag('config', 'G-RPTB8H6JGP')"


def main() -> int:
    issues = []
    measured = 0
    for path in sorted(ROOT.rglob("*.html")):
        html = path.read_text(encoding="utf-8")
        if not re.search(r"</body\s*>", html, flags=re.IGNORECASE):
            # Arquivos de verificacao de propriedade podem nao ter corpo HTML.
            if BEACON in html:
                issues.append(f"{path}: beacon fora de uma pagina HTML")
            continue
        count = html.count(BEACON)
        google_count = html.count(GOOGLE)
        config_count = html.count(GA_CONFIG)
        if count != 1 or google_count != 1 or config_count != 1:
            issues.append(f"{path.relative_to(ROOT)}: Cloudflare={count}, Google={google_count}, GA4 config={config_count}; esperado 1 de cada")
        else:
            measured += 1
    print(f"Paginas com Cloudflare e Google Analytics GA4: {measured}")
    print(f"Erros de instalacao do contador: {len(issues)}")
    for issue in issues[:30]:
        print("  " + issue)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())

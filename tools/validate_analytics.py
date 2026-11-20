"""Confere se o Cloudflare Web Analytics foi incluido exatamente uma vez por pagina."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "_site"
BEACON = "https://static.cloudflareinsights.com/beacon.min.js"
TOKEN_PATTERN = re.compile(r'data-cf-beacon=[\\'"][^\\'"]*token', re.IGNORECASE)


def main() -> int:
    issues = []
    measured = 0
    for path in sorted(ROOT.rglob("*.html")):
        html = path.read_text(encoding="utf-8")
        if not re.search(r"</body\\s*>", html, flags=re.IGNORECASE):
            # Arquivos de verificacao de propriedade podem nao ter corpo HTML.
            if BEACON in html:
                issues.append(f"{path}: beacon fora de uma pagina HTML")
            continue
        count = html.count(BEACON)
        if count != 1:
            issues.append(f"{path.relative_to(ROOT)}: {count} scripts de analytics (esperado: 1)")
        else:
            measured += 1
    print(f"Paginas com coleta Cloudflare: {measured}")
    print(f"Erros de instalacao do contador: {len(issues)}")
    for issue in issues[:30]:
        print("  " + issue)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())

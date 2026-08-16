from __future__ import annotations

import html
import os
import re
import shutil
import sys
import tomllib
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import quote
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup, NavigableString, Tag

try:
    import markdown as _markdown
except ImportError:
    _markdown = None
try:
    import mistune as _mistune
except ImportError:
    _mistune = None

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
BASE_URL = "https://jorgeluisfernandes-dev.github.io/afinidadeseletivas/"

CATEGORY_DIR = {
    "BlogsFeras": "blogsferas",
    "Conto": "conto",
    "Crônica": "cronica",
    "Humor": "humor",
    "Musica": "musica",
    "Poemas da Cabra": "poemas_da_cabra",
    "PoesiasEletivas": "poesiaseletivas",
    "PoetasAfins": "poetasafins",
    "Projeto": "projeto",
    "Tese": "tese",
}

POETRY_CATEGORIES = {"Poemas da Cabra", "PoesiasEletivas", "PoetasAfins"}
SKIP_TOP = {".git", ".github", "content", "templates", "tools", "_site"}
SKIP_FILES = {"requirements.txt", "NOVAS_PUBLICACOES.md", "README.md"}
MONTHS = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

@dataclass
class Post:
    source: Path
    title: str
    day: date
    category: str
    tags: list[str]
    kind: str
    summary: str
    body_md: str
    slug: str
    relpath: PurePosixPath

    @property
    def url(self) -> str:
        return BASE_URL + quote(str(self.relpath))


@dataclass
class SitePost:
    path: Path
    relpath: PurePosixPath
    title: str
    day: date
    category: str


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or "texto"


def parse_post(path: Path) -> Post:
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"\A\+\+\+\s*\n(.*?)\n\+\+\+\s*\n?(.*)\Z", raw, flags=re.S)
    if not m:
        raise ValueError(f"{path}: cabeçalho TOML entre +++ não encontrado")
    meta = tomllib.loads(m.group(1))
    body = m.group(2).strip()

    required = ["title", "date", "category"]
    missing = [k for k in required if k not in meta]
    if missing:
        raise ValueError(f"{path}: faltam campos: {', '.join(missing)}")

    d = meta["date"]
    if isinstance(d, datetime):
        d = d.date()
    elif isinstance(d, str):
        d = date.fromisoformat(d)
    if not isinstance(d, date):
        raise ValueError(f"{path}: data inválida")

    category = str(meta["category"])
    if category not in CATEGORY_DIR:
        raise ValueError(f"{path}: categoria não reconhecida: {category}")

    kind = str(meta.get("kind", "poetry" if category in POETRY_CATEGORIES else "prose")).lower()
    if kind not in {"prose", "poetry"}:
        raise ValueError(f"{path}: kind deve ser prose ou poetry")

    title = str(meta["title"]).strip()
    slug = slugify(str(meta.get("slug", title)))
    tags = [str(x).strip() for x in meta.get("tags", []) if str(x).strip()]
    summary = str(meta.get("summary", "")).strip()
    if not summary:
        plain = re.sub(r"[`*_>#\[\]()!-]", " ", body)
        plain = re.sub(r"\s+", " ", plain).strip()
        summary = plain[:300].rstrip() + ("…" if len(plain) > 300 else "")

    rel = PurePosixPath("archive") / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.day:02d}" / f"{slug}.html"
    return Post(path, title, d, category, tags, kind, summary, body, slug, rel)


def load_posts() -> list[Post]:
    posts_dir = ROOT / "content" / "posts"
    posts = []
    for path in sorted(posts_dir.glob("*.md")):
        if path.name.startswith("_") or path.name.lower() == "readme.md":
            continue
        posts.append(parse_post(path))
    posts.sort(key=lambda p: (p.day, p.title.lower()))
    seen = set()
    for p in posts:
        if p.relpath in seen:
            raise ValueError(f"URL duplicada entre novos textos: {p.relpath}")
        seen.add(p.relpath)
    return posts


def copy_public_site() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for item in ROOT.iterdir():
        if item.name in SKIP_TOP or item.name in SKIP_FILES:
            continue
        target = OUT / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        elif item.is_file():
            shutil.copy2(item, target)


def soup_file(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def write_soup(path: Path, soup: BeautifulSoup) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(soup), encoding="utf-8")


def html_fragment(markup: str) -> list[Tag | NavigableString]:
    frag = BeautifulSoup(markup, "html.parser")
    return list(frag.contents)


def render_body(post: Post) -> str:
    extensions = ["extra", "sane_lists"]
    if post.kind == "poetry":
        # dois espaços no fim de cada verso forçam quebra sem transformar cada linha em parágrafo
        blocks = []
        for block in re.split(r"\n\s*\n", post.body_md.strip()):
            lines = block.splitlines()
            if lines and not any(line.lstrip().startswith(("#", ">", "- ", "* ")) for line in lines):
                block = "  \n".join(lines)
            blocks.append(block)
        text = "\n\n".join(blocks)
    else:
        text = post.body_md
    if _markdown is not None:
        return _markdown.markdown(text, extensions=extensions, output_format="html5")
    if _mistune is not None:
        renderer = _mistune.create_markdown(escape=False, hard_wrap=False)
        return renderer(text)
    raise RuntimeError("Instale a dependência Markdown: pip install -r requirements.txt")


def relroot_for_post() -> str:
    return "../../../../"


def make_post_page(post: Post) -> None:
    template_rel = "archive/2007/05/06/o-salto.html" if post.kind == "poetry" else "archive/2007/10/16/orion.html"
    template = OUT / template_rel
    soup = soup_file(template)
    root = relroot_for_post()

    if soup.title:
        soup.title.string = f"{post.title} — AfinidadeSeletivas"
    desc = soup.find("meta", attrs={"name": "description"})
    if desc:
        desc["content"] = post.summary
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if not canonical:
        canonical = soup.new_tag("link", rel="canonical", href=post.url)
        soup.head.append(canonical)
    else:
        canonical["href"] = post.url

    body = soup.body
    body["class"] = ["prototype-2026", "poem-post" if post.kind == "poetry" else "prose-post", f"prose-{CATEGORY_DIR[post.category]}"]

    date_el = soup.select_one(".content .date")
    date_el.string = post.day.strftime("%d/%m/%Y")
    title_el = soup.select_one(".content .post-title")
    title_el.clear(); title_el.append(post.title)
    context = soup.select_one(".content .post-context")
    context.string = f"{post.category} · publicado em {post.day.strftime('%d/%m/%Y')}"

    article = soup.select_one("article.post-body")
    article.clear()
    for node in html_fragment(render_body(post)):
        article.append(node)

    posted = soup.select_one(".posted")
    posted.clear()
    posted.append("Escrito em ")
    cat_a = soup.new_tag("a", href=f"{root}{CATEGORY_DIR[post.category]}/index.html")
    cat_a.string = post.category
    posted.append(cat_a)
    if post.tags:
        posted.append(" | Tags: ")
        for i, tag in enumerate(post.tags):
            if i:
                posted.append(" ")
            a = soup.new_tag("a", href=f"{root}tags/{slugify(tag)}/index.html")
            a["class"] = ["tag"]; a.string = tag
            posted.append(a)

    nav = soup.select_one(".post-navigation")
    if nav:
        nav.clear()
        older = soup.new_tag("div"); older["class"] = ["older"]
        category = soup.new_tag("div"); category["class"] = ["category"]
        lab = soup.new_tag("span"); lab["class"] = ["nav-label"]; lab.string = "Categoria"; category.append(lab)
        ca = soup.new_tag("a", href=f"{root}{CATEGORY_DIR[post.category]}/index.html"); ca.string = post.category; category.append(ca)
        newer = soup.new_tag("div"); newer["class"] = ["newer"]
        nav.append(older); nav.append(category); nav.append(newer)

    write_soup(OUT / Path(str(post.relpath)), soup)


def make_card(soup: BeautifulSoup, post: Post, prefix: str = "") -> Tag:
    art = soup.new_tag("article"); art["class"] = ["post-card"]
    meta = soup.new_tag("div"); meta["class"] = ["meta"]; meta.string = f"{post.day.strftime('%d/%m/%Y')} — {post.category}"; art.append(meta)
    h3 = soup.new_tag("h3"); a = soup.new_tag("a", href=f"{prefix}{post.relpath}"); a.string = post.title; h3.append(a); art.append(h3)
    p = soup.new_tag("p"); p.string = post.summary; art.append(p)
    if post.tags:
        d = soup.new_tag("div")
        for tag in post.tags:
            s = soup.new_tag("span"); s["class"] = ["tag"]; s.string = tag; d.append(s); d.append(" ")
        art.append(d)
    return art


def update_home(posts: list[Post]) -> None:
    if not posts:
        return
    path = OUT / "index.html"; soup = soup_file(path)
    content = soup.select_one("main .content")
    old = soup.find("h2", class_="generated-new-posts-title")
    if old:
        cur = old
        while cur:
            nxt = cur.next_sibling
            if isinstance(nxt, Tag) and nxt.name == "h2" and "home-section-title" in (nxt.get("class") or []):
                break
            cur.extract(); cur = nxt
    anchor = None
    for h in content.find_all("h2", class_="home-section-title", recursive=False):
        if "Do acervo" in h.get_text(" ", strip=True):
            anchor = h; break
    title = soup.new_tag("h2"); title["class"] = ["home-section-title", "generated-new-posts-title"]; title.string = "Novas publicações"
    anchor.insert_before(title)
    for p in sorted(posts, key=lambda x: (x.day, x.title.lower()), reverse=True)[:10]:
        anchor.insert_before(make_card(soup, p))
    write_soup(path, soup)


def update_category_pages(posts: list[Post]) -> None:
    by_cat = {}
    for p in posts:
        by_cat.setdefault(p.category, []).append(p)
    for category, items in by_cat.items():
        path = OUT / CATEGORY_DIR[category] / "index.html"
        soup = soup_file(path)
        content = soup.select_one("main .content")
        first_card = content.find("article", class_="post-card", recursive=False)
        for p in sorted(items, key=lambda x: (x.day, x.title.lower()), reverse=True):
            card = make_card(soup, p, prefix="../")
            if first_card:
                first_card.insert_before(card)
            else:
                content.append(card)
        deck = soup.select_one(".page-deck .small")
        if deck:
            m = re.search(r"(\d+)", deck.get_text())
            if m:
                deck.string = re.sub(r"\d+", str(int(m.group(1)) + len(items)), deck.get_text())
        write_soup(path, soup)


def update_archive(posts: list[Post]) -> None:
    if not posts:
        return
    path = OUT / "arquivo" / "index.html"; soup = soup_file(path)
    content = soup.select_one("main .content")
    first_year = content.find("h3", class_="year-heading", recursive=False)
    grouped = {}
    for p in posts:
        grouped.setdefault((p.day.year, p.day.month), []).append(p)
    years = sorted({y for y, _ in grouped}, reverse=True)
    insert_nodes = []
    for y in years:
        hy = soup.new_tag("h3"); hy["class"] = ["year-heading"]; hy.string = str(y); insert_nodes.append(hy)
        for m in sorted([m for yy, m in grouped if yy == y], reverse=True):
            hm = soup.new_tag("h4", id=f"{y:04d}-{m:02d}"); hm["class"] = ["month-heading"]; hm.string = MONTHS[m]; insert_nodes.append(hm)
            ul = soup.new_tag("ul"); ul["class"] = ["archive-list"]
            for p in sorted(grouped[(y, m)], key=lambda x: (x.day, x.title.lower()), reverse=True):
                li = soup.new_tag("li")
                sp = soup.new_tag("span"); sp["class"] = ["archive-date"]; sp.string = p.day.strftime("%d/%m/%Y"); li.append(sp)
                a = soup.new_tag("a", href=f"../{p.relpath}"); a.string = p.title; li.append(a); li.append(" ")
                c = soup.new_tag("span"); c["class"] = ["small"]; c.string = f"[{p.category}]"; li.append(c)
                ul.append(li)
            insert_nodes.append(ul)
    for node in reversed(insert_nodes):
        first_year.insert_before(node)
    deck = soup.select_one(".page-deck")
    if deck:
        old = deck.get_text(" ", strip=True)
        m = re.search(r"\b(\d+)\b", old)
        if m:
            total = int(m.group(1)) + len(posts)
            deck.string = f"{total} textos organizados por data."
    write_soup(path, soup)


def update_tags(posts: list[Post]) -> None:
    for p in posts:
        for tag in p.tags:
            slug = slugify(tag)
            path = OUT / "tags" / slug / "index.html"
            if path.exists():
                soup = soup_file(path)
                content = soup.select_one("main .content")
                first_card = content.find("article", class_="post-card", recursive=False)
                card = make_card(soup, p, prefix="../../")
                if first_card: first_card.insert_before(card)
                else: content.append(card)
                write_soup(path, soup)
            else:
                # clona uma página de tag apenas para manter a identidade visual
                sample = next((x for x in (OUT / "tags").glob("*/index.html") if x.is_file()), None)
                if not sample:
                    continue
                soup = soup_file(sample)
                if soup.title: soup.title.string = f"Tag: {tag} — AfinidadeSeletivas"
                title = soup.select_one(".page-title")
                if title: title.string = f"Tag: {tag}"
                content = soup.select_one("main .content")
                for card in list(content.find_all("article", class_="post-card", recursive=False)): card.decompose()
                content.append(make_card(soup, p, prefix="../../"))
                write_soup(path, soup)


def update_recent_sidebar(posts: list[Post]) -> None:
    if not posts:
        return
    latest_new = sorted(posts, key=lambda x: (x.day, x.title.lower()), reverse=True)
    for path in OUT.rglob("*.html"):
        soup = soup_file(path)
        box = None
        for b in soup.select(".rightbar .box"):
            h = b.find("h2")
            if h and h.get_text(" ", strip=True) == "Mensagens recentes": box = b; break
        if not box:
            continue
        ul = box.find("ul")
        old_items = list(ul.find_all("li", recursive=False)) if ul else []
        if not ul: continue
        ul.clear()
        rel = os.path.relpath(OUT, path.parent).replace("\\", "/")
        prefix = "" if rel == "." else rel.rstrip("/") + "/"
        for p in latest_new[:8]:
            li = soup.new_tag("li"); a = soup.new_tag("a", href=f"{prefix}{p.relpath}"); a.string = p.title; li.append(a); ul.append(li)
        remaining = max(0, 8 - min(8, len(latest_new)))
        for li in old_items[:remaining]: ul.append(li)
        write_soup(path, soup)


def collect_site_posts() -> list[SitePost]:
    items: list[SitePost] = []
    archive = OUT / "archive"
    if not archive.exists():
        return items
    for path in archive.glob("[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]/*.html"):
        soup = soup_file(path)
        title_el = soup.select_one(".post-title")
        date_el = soup.select_one(".date")
        context = soup.select_one(".post-context")
        if not title_el or not date_el:
            continue
        try:
            d = datetime.strptime(date_el.get_text(" ", strip=True), "%d/%m/%Y").date()
        except ValueError:
            continue
        category = ""
        if context:
            category = context.get_text(" ", strip=True).split("·", 1)[0].strip()
        if category not in CATEGORY_DIR:
            posted = soup.select_one(".posted a")
            category = posted.get_text(" ", strip=True) if posted else ""
        if category not in CATEGORY_DIR:
            continue
        rel = PurePosixPath(path.relative_to(OUT).as_posix())
        items.append(SitePost(path, rel, title_el.get_text(" ", strip=True), d, category))
    items.sort(key=lambda p: (p.day, p.title.casefold(), str(p.relpath)))
    return items


def _set_nav_side(soup: BeautifulSoup, container: Tag, label: str, text: str, href: str) -> None:
    container.clear()
    lab = soup.new_tag("span"); lab["class"] = ["nav-label"]; lab.string = label; container.append(lab)
    a = soup.new_tag("a", href=href); a.string = text; container.append(a)


def update_new_post_navigation(new_posts: list[Post]) -> None:
    if not new_posts:
        return
    site_posts = collect_site_posts()
    new_rel = {str(p.relpath) for p in new_posts}
    historical = [p for p in site_posts if str(p.relpath) not in new_rel]
    ordered_new = sorted(new_posts, key=lambda p: (p.day, p.title.casefold(), str(p.relpath)))

    # Cada texto novo conhece seu vizinho cronológico; o acervo antigo permanece intocado,
    # exceto pelo último texto anterior, que ganha a ponte para a primeira publicação nova.
    for i, post in enumerate(ordered_new):
        path = OUT / Path(str(post.relpath)); soup = soup_file(path)
        nav = soup.select_one(".post-navigation")
        if not nav:
            continue
        older_box = nav.select_one(".older"); newer_box = nav.select_one(".newer")
        older_candidates = [x for x in historical if (x.day, x.title.casefold()) <= (post.day, post.title.casefold())]
        older = ordered_new[i - 1] if i > 0 else (older_candidates[-1] if older_candidates else None)
        newer = ordered_new[i + 1] if i + 1 < len(ordered_new) else None
        if older_box:
            older_box.clear()
            if older:
                if isinstance(older, Post):
                    href = f"../../../../{older.relpath}"
                    title = older.title
                else:
                    href = f"../../../../{older.relpath}"
                    title = older.title
                _set_nav_side(soup, older_box, "Anterior (mais antigo)", f"← {title}", href)
        if newer_box:
            newer_box.clear()
            if newer:
                _set_nav_side(soup, newer_box, "Próximo (mais recente)", f"{newer.title} →", f"../../../../{newer.relpath}")
        write_soup(path, soup)

    first = ordered_new[0]
    previous = [x for x in historical if (x.day, x.title.casefold()) <= (first.day, first.title.casefold())]
    if previous:
        old = previous[-1]
        soup = soup_file(old.path)
        nav = soup.select_one(".post-navigation")
        newer_box = nav.select_one(".newer") if nav else None
        if newer_box:
            relroot = os.path.relpath(OUT, old.path.parent).replace("\\", "/")
            prefix = "" if relroot == "." else relroot.rstrip("/") + "/"
            _set_nav_side(soup, newer_box, "Próximo (mais recente)", f"{first.title} →", f"{prefix}{first.relpath}")
            write_soup(old.path, soup)


def update_global_counts_and_archive_sidebar() -> None:
    posts = collect_site_posts()
    cat_counts = {c: 0 for c in CATEGORY_DIR}
    month_counts: dict[tuple[int, int], int] = {}
    for p in posts:
        cat_counts[p.category] += 1
        month_counts[(p.day.year, p.day.month)] = month_counts.get((p.day.year, p.day.month), 0) + 1

    for path in OUT.rglob("*.html"):
        soup = soup_file(path)
        changed = False

        # Contadores da caixa Categorias em qualquer página.
        for box in soup.select(".rightbar .box"):
            h = box.find("h2")
            if not h:
                continue
            title = h.get_text(" ", strip=True)
            if title == "Categorias":
                for li in box.select("ul > li"):
                    a = li.find("a")
                    span = li.find("span", class_="small")
                    if a and span and a.get_text(" ", strip=True) in cat_counts:
                        span.string = f"({cat_counts[a.get_text(' ', strip=True)]})"
                        changed = True
            elif title == "Arquivo":
                content = box.select_one(".boxcontent")
                if content:
                    content.clear()
                    rel = os.path.relpath(OUT, path.parent).replace("\\", "/")
                    prefix = "" if rel == "." else rel.rstrip("/") + "/"
                    for year in sorted({y for y, _ in month_counts}, reverse=True):
                        ydiv = soup.new_tag("div"); ydiv["class"] = ["archive-year"]; ydiv.string = str(year); content.append(ydiv)
                        for month in sorted([m for y, m in month_counts if y == year], reverse=True):
                            mdiv = soup.new_tag("div"); mdiv["class"] = ["archive-month"]
                            a = soup.new_tag("a", href=f"{prefix}arquivo/index.html#{year:04d}-{month:02d}")
                            a.string = f"{MONTHS[month]}: {month_counts[(year, month)]}"
                            mdiv.append(a); content.append(mdiv)
                    changed = True

        # Contadores dos Caminhos de leitura da página inicial.
        if path == OUT / "index.html":
            for card in soup.select(".reading-path"):
                a = card.find("a")
                span = card.find("span", class_="small")
                if a and span and a.get_text(" ", strip=True) in cat_counts:
                    span.string = f"({cat_counts[a.get_text(' ', strip=True)]})"
                    changed = True

        if changed:
            write_soup(path, soup)


def update_tags_index(posts: list[Post]) -> None:
    if not posts:
        return
    path = OUT / "tags" / "index.html"
    if not path.exists():
        return
    soup = soup_file(path)
    holder = soup.select_one("main .content p")
    if not holder:
        return

    entries: dict[str, tuple[str, int]] = {}
    for a in holder.find_all("a", class_="tag", recursive=False):
        href = a.get("href", "")
        slug = href.split("/", 1)[0]
        txt = a.get_text(" ", strip=True)
        m = re.match(r"(.*)\s+\((\d+)\)$", txt)
        if slug and m:
            entries[slug] = (m.group(1).strip(), int(m.group(2)))

    for post in posts:
        for tag in post.tags:
            slug = slugify(tag)
            if slug in entries:
                label, count = entries[slug]
                entries[slug] = (label, count + 1)
            else:
                entries[slug] = (tag, 1)

    holder.clear()
    for slug, (label, count) in sorted(entries.items(), key=lambda x: x[1][0].casefold()):
        a = soup.new_tag("a", href=f"{slug}/index.html"); a["class"] = ["tag"]; a.string = f"{label} ({count})"
        holder.append(a); holder.append(" ")
    write_soup(path, soup)


def generate_sitemap() -> None:
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for path in sorted(OUT.rglob("*.html")):
        rel = path.relative_to(OUT).as_posix()
        if rel == "404.html" or rel.endswith("/404.html"):
            continue
        if rel.endswith("/index.html"):
            web = rel[:-10]
        elif rel == "index.html":
            web = ""
        else:
            web = rel
        u = ET.SubElement(urlset, "url")
        ET.SubElement(u, "loc").text = BASE_URL + quote(web)
    ET.ElementTree(urlset).write(OUT / "sitemap.xml", encoding="utf-8", xml_declaration=True)


def generate_rss(posts: list[Post]) -> None:
    rss = ET.Element("rss", version="2.0"); ch = ET.SubElement(rss, "channel")
    ET.SubElement(ch, "title").text = "AfinidadeSeletivas"
    ET.SubElement(ch, "link").text = BASE_URL
    ET.SubElement(ch, "description").text = "Poesia, prosa e afinidades."
    for p in sorted(posts, key=lambda x: (x.day, x.title.lower()), reverse=True)[:20]:
        item = ET.SubElement(ch, "item")
        ET.SubElement(item, "title").text = p.title
        ET.SubElement(item, "link").text = p.url
        ET.SubElement(item, "guid").text = p.url
        dt = datetime(p.day.year, p.day.month, p.day.day, tzinfo=timezone.utc)
        ET.SubElement(item, "pubDate").text = dt.strftime("%a, %d %b %Y 00:00:00 +0000")
        ET.SubElement(item, "description").text = p.summary
    ET.ElementTree(rss).write(OUT / "rss.xml", encoding="utf-8", xml_declaration=True)


def main() -> int:
    posts = load_posts()
    copy_public_site()
    for p in posts:
        make_post_page(p)
    update_home(posts)
    update_category_pages(posts)
    update_archive(posts)
    update_tags(posts)
    update_tags_index(posts)
    update_recent_sidebar(posts)
    update_new_post_navigation(posts)
    update_global_counts_and_archive_sidebar()
    generate_sitemap()
    generate_rss(posts)
    print(f"Site montado em {OUT}")
    print(f"Novas publicações encontradas: {len(posts)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise

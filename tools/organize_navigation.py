"""Cria os caminhos de leitura e os índices sem mudar os URLs dos textos."""

from __future__ import annotations

import json
import os
from pathlib import Path

from bs4 import BeautifulSoup

from build_site import OUT, ROOT, collect_site_posts, generate_sitemap

WORK = [
    ("PoesiasEletivas", "poesiaseletivas", "Poemas escritos para o blog."),
    ("Contos", "conto", "Narrativas breves e ficção."),
    ("Crônicas", "cronica", "Observações do cotidiano."),
    ("Ensaios", "tese", "Argumentos e textos de reflexão."),
    ("Projetos", "projeto", "Ideias e propostas para o mundo comum."),
    ("Humor", "humor", "Textos de humor do acervo."),
    ("Música", "musica", "A música entre os textos do blog."),
]
AFFINITIES = [
    ("Poetas Afins", "poetasafins", "Poemas de outros autores e acesso às coleções individuais."),
    ("Leituras", "leituras", "Links escolhidos da antiga blogsfera e de hoje."),
    ("Blogsfera", "blogsferas", "Notas e conversas com outros blogs."),
]
INDEXES = [
    ("Autores", "autores", "Coleções de poetas em ordem alfabética."),
    ("Temas", "temas", "Alguns percursos temáticos pelo acervo."),
    ("Tags", "tags", "Todos os termos usados para localizar textos."),
    ("Busca", "busca", "Pesquise palavras nos títulos, resumos, tags e categorias."),
]
TOPICS = [
    ("Poesia brasileira", "poesia-brasileira"),
    ("Poesia traduzida", "poesia-traduzida"),
    ("Linguagem", "linguagem"),
    ("Memória", "memoria"),
    ("Filosofia", "filosofia"),
    ("Psicologia", "psicologia"),
    ("Consciência", "consciencia"),
    ("Inteligência artificial", "inteligencia-artificial"),
    ("Maranhão", "maranhao"),
    ("São Luís", "sao-luis"),
]


def read(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def write(path: Path, soup: BeautifulSoup) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(soup), encoding="utf-8")


def new_page(directory: str, title: str, description: str) -> tuple[BeautifulSoup, object]:
    soup = read(OUT / "poetasafins" / "index.html")
    soup.title.string = f"{title} — AfinidadeSeletivas"
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        meta["content"] = description
    soup.body["class"] = ["site-2026", "section-page"]
    content = soup.select_one("main .content")
    content.clear()
    h2 = soup.new_tag("h2", attrs={"class": "page-title"})
    h2.string = title
    content.append(h2)
    return soup, content


def add_intro(soup: BeautifulSoup, content: object, text: str) -> None:
    p = soup.new_tag("p", attrs={"class": "section-intro"})
    p.string = text
    content.append(p)


def add_links(soup: BeautifulSoup, content: object, entries: list[tuple[str, str, str]], prefix: str = "../") -> None:
    holder = soup.new_tag("div", attrs={"class": "section-links"})
    for name, directory, description in entries:
        article = soup.new_tag("article", attrs={"class": "section-link"})
        h3 = soup.new_tag("h3")
        a = soup.new_tag("a", href=f"{prefix}{directory}/index.html")
        a.string = name
        h3.append(a)
        article.append(h3)
        p = soup.new_tag("p")
        p.string = description
        article.append(p)
        holder.append(article)
    content.append(holder)


def make_hubs() -> None:
    for directory, title, intro, links in [
        ("obra", "Obra", "Poesia, prosa e outras formas do que foi escrito aqui.", WORK),
        ("afinidades", "Afinidades", "O que foi encontrado na escrita dos outros e nas conversas do blog.", AFFINITIES),
        ("indices", "Índices", "Encontre textos pelo autor, assunto, tag ou palavra.", INDEXES),
    ]:
        soup, content = new_page(directory, title, intro)
        add_intro(soup, content, intro)
        add_links(soup, content, links)
        write(OUT / directory / "index.html", soup)


def name_collections() -> None:
    for directory, display in [("conto", "Contos"), ("cronica", "Crônicas"),
                               ("tese", "Ensaios"), ("projeto", "Projetos"),
                               ("blogsferas", "Blogsfera"), ("poetasafins", "Poetas Afins")]:
        path = OUT / directory / "index.html"
        soup = read(path)
        soup.title.string = f"{display} — AfinidadeSeletivas"
        soup.select_one(".page-title").string = display
        write(path, soup)


def make_readings() -> None:
    soup, content = new_page("leituras", "Leituras", "Links escolhidos pelo AfinidadeSeletivas.")
    add_intro(soup, content, "Uma seleção de blogs e páginas literárias que acompanham o percurso do site.")
    original = read(OUT / "index.html")
    box = original.select_one(".curated-box .boxcontent")
    if not box:
        raise RuntimeError("Seleção de leituras não encontrada no site")
    for item in box.contents:
        content.append(BeautifulSoup(str(item), "html.parser"))
    write(OUT / "leituras" / "index.html", soup)


def make_topics() -> None:
    soup, content = new_page("temas", "Temas", "Percursos temáticos escolhidos entre as tags do blog.")
    add_intro(soup, content, "Uma entrada por assunto. A lista completa de termos está em Tags.")
    entries = []
    for label, slug in TOPICS:
        target = OUT / "tags" / slug / "index.html"
        if not target.exists():
            raise RuntimeError(f"Tema sem página de tag: {slug}")
        count = len(read(target).select("main .post-card"))
        entries.append((label, f"tags/{slug}", f"{count} texto{'s' if count != 1 else ''} sob este termo."))
    add_links(soup, content, entries)
    write(OUT / "temas" / "index.html", soup)


def make_search() -> None:
    items = []
    for post in collect_site_posts():
        page = read(post.path)
        description = page.find("meta", attrs={"name": "description"})
        items.append({
            "title": post.title,
            "url": f"../{post.relpath}",
            "date": post.day.strftime("%d/%m/%Y"),
            "category": post.category,
            "summary": description.get("content", "") if description else "",
            "tags": [a.get_text(" ", strip=True) for a in page.select(".posted a.tag")],
        })
    directory = OUT / "busca"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "indice.json").write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    soup, content = new_page("busca", "Busca", "Pesquise no acervo do AfinidadeSeletivas.")
    add_intro(soup, content, f"Pesquise títulos, resumos, tags e categorias de {len(items)} textos.")
    form = BeautifulSoup(
        '<form class="search-form" role="search"><label for="query">Palavra ou expressão</label>'
        '<input id="query" name="q" type="search" autocomplete="off" minlength="2" '
        'placeholder="Ex.: João Cabral, linguagem, memória"/>'
        '<button type="submit">Buscar</button></form>'
        '<p id="search-status" class="search-status" role="status">Digite ao menos duas letras para começar.</p>'
        '<div id="search-results" class="search-results"></div>',
        "html.parser",
    )
    content.extend(list(form.contents))
    script = soup.new_tag("script", src="../assets/search.js", defer=True)
    soup.body.append(script)
    write(directory / "index.html", soup)


def make_manifesto() -> None:
    home = read(OUT / "index.html")
    manifesto = read(ROOT / "index.html").select_one(".home-manifesto")
    if not manifesto:
        raise RuntimeError("Manifesto original não encontrado na abertura")
    soup, content = new_page("manifesto", "Manifesto", "Por que escrever e escolher afinidades.")
    original_about = read(ROOT / "sobre" / "index.html")
    quotes = original_about.select_one(".about-quotes")
    if quotes:
        content.append(BeautifulSoup(str(quotes), "html.parser"))
    content.append(BeautifulSoup(str(manifesto), "html.parser"))
    write(OUT / "manifesto" / "index.html", soup)

    teaser = home.new_tag("section", attrs={"class": "home-intro"})
    opening = home.new_tag("p")
    opening.string = manifesto.find("p").get_text(" ", strip=True)
    teaser.append(opening)
    p = home.new_tag("p")
    a = home.new_tag("a", href="manifesto/index.html")
    a.string = "Leia o manifesto →"
    p.append(a)
    teaser.append(p)
    current = home.select_one(".home-manifesto, .home-intro")
    if not current:
        raise RuntimeError("Abertura do blog não encontrada")
    current.replace_with(teaser)

    paths = home.select_one(".reading-paths")
    if paths:
        paths.clear()
        for name, directory, desc in [
            ("Obra", "obra", "Poesias, contos, crônicas, ensaios e projetos."),
            ("Afinidades", "afinidades", "Poetas, leituras e blogs em diálogo."),
            ("Arquivo", "arquivo", "Os textos organizados por ano e mês."),
            ("Índices", "indices", "Autores, temas, tags e busca."),
        ]:
            card = home.new_tag("div", attrs={"class": "reading-path"})
            h3 = home.new_tag("h3")
            link = home.new_tag("a", href=f"{directory}/index.html")
            link.string = name
            h3.append(link)
            card.append(h3)
            p = home.new_tag("p")
            p.string = desc
            card.append(p)
            paths.append(card)
    write(OUT / "index.html", home)

    old = OUT / "sobre" / "index.html"
    old.write_text(
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url=../manifesto/index.html">'
        '<link rel="canonical" href="https://afinidadeseletivas.com/manifesto/">'
        '<title>Manifesto — AfinidadeSeletivas</title></head><body>'
        '<p>O antigo Sobre está no <a href="../manifesto/index.html">Manifesto</a>.</p>'
        '</body></html>',
        encoding="utf-8",
    )


def navigation() -> None:
    for path in OUT.rglob("*.html"):
        soup = read(path)
        nav = soup.select_one(".navtop")
        if not nav:
            continue
        prefix = os.path.relpath(OUT, path.parent).replace("\\", "/")
        prefix = "" if prefix == "." else prefix.rstrip("/") + "/"
        relative = path.relative_to(OUT).as_posix()
        section = relative.split("/", 1)[0]
        if section in {"obra", "conto", "cronica", "tese", "projeto", "humor", "musica", "poesiaseletivas"}:
            active = "Obra"
        elif section in {"afinidades", "poetasafins", "leituras", "blogsferas"} or section.startswith("afins_"):
            active = "Afinidades"
        elif section == "arquivo":
            active = "Arquivo"
        elif section in {"indices", "autores", "temas", "tags", "busca"}:
            active = "Índices"
        elif section == "manifesto":
            active = "Manifesto"
        else:
            active = "Início" if relative == "index.html" else None
        nav.clear()
        for label, directory in [("Início", ""), ("Obra", "obra/"), ("Afinidades", "afinidades/"),
                                 ("Arquivo", "arquivo/"), ("Índices", "indices/"), ("Manifesto", "manifesto/")]:
            link = soup.new_tag("a", href=f"{prefix}{directory}index.html")
            link.string = label
            if label == active:
                link["aria-current"] = "page"
            nav.append(link)

        category_box = next((box for box in soup.select(".rightbar .box")
                             if box.h2 and box.h2.get_text(" ", strip=True) == "Categorias"), None)
        if category_box:
            counts = {}
            for li in category_box.select("li"):
                a = li.find("a")
                small = li.find("span", class_="small")
                if a and small:
                    counts[a.get_text(" ", strip=True)] = small.get_text(" ", strip=True)
            groups = [
                ("Obra", "obra", [(name, directory, counts.get(key, "")) for name, directory, key in [
                    ("PoesiasEletivas", "poesiaseletivas", "PoesiasEletivas"), ("Contos", "conto", "Conto"),
                    ("Crônicas", "cronica", "Crônica"), ("Ensaios", "tese", "Tese"),
                    ("Projetos", "projeto", "Projeto"), ("Humor", "humor", "Humor"), ("Música", "musica", "Musica")]]),
                ("Afinidades", "afinidades", [("Poetas Afins", "poetasafins", counts.get("PoetasAfins", "")),
                    ("Leituras", "leituras", ""), ("Blogsfera", "blogsferas", counts.get("BlogsFeras", ""))]),
                ("Índices", "indices", [("Autores", "autores", counts.get("Autores", "")),
                    ("Temas", "temas", ""), ("Tags", "tags", ""), ("Busca", "busca", "")]),
            ]
            for heading, directory, entries in reversed(groups):
                box = soup.new_tag("div", attrs={"class": "box"})
                h2 = soup.new_tag("h2")
                head_link = soup.new_tag("a", href=f"{prefix}{directory}/index.html")
                head_link.string = heading
                h2.append(head_link)
                box.append(h2)
                wrapper = soup.new_tag("div", attrs={"class": "boxcontent"})
                ul = soup.new_tag("ul")
                for label, subdir, count in entries:
                    li = soup.new_tag("li")
                    a = soup.new_tag("a", href=f"{prefix}{subdir}/index.html")
                    a.string = label
                    li.append(a)
                    if count:
                        li.append(" ")
                        small = soup.new_tag("span", attrs={"class": "small"})
                        small.string = count
                        li.append(small)
                    ul.append(li)
                wrapper.append(ul)
                box.append(wrapper)
                category_box.insert_after(box)
            category_box.decompose()

        for a in soup.select(".footer a"):
            if a.get_text(" ", strip=True) == "Sobre o blog":
                a.string = "Manifesto"
                a["href"] = f"{prefix}manifesto/index.html"
        write(path, soup)


def main() -> int:
    make_hubs()
    name_collections()
    make_readings()
    make_topics()
    make_search()
    make_manifesto()
    navigation()
    generate_sitemap()
    print("Navegação organizada: Obra, Afinidades, Arquivo, Índices e Manifesto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

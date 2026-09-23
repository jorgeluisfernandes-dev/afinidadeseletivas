"""Organiza o catálogo de poetas no site montado, mantendo os URLs históricos."""

from __future__ import annotations

import os
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup

from build_site import AFINS_AUTHOR_SLUGS, CATEGORY_DIR, OUT, ROOT, generate_sitemap

JOAO = "Afins_João Cabral de Melo Neto"
OLD_CATEGORY = "Poemas da Cabra"
OLD_POST = "archive/2007/11/07/poema-s-da-cabra.html"


def read(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def write(path: Path, soup: BeautifulSoup) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(soup), encoding="utf-8")


def author_key(name: str) -> str:
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").casefold()


def migrate_joao() -> None:
    old_path = OUT / CATEGORY_DIR[OLD_CATEGORY] / "index.html"
    legacy_source = ROOT / CATEGORY_DIR[OLD_CATEGORY] / "index.html"
    new_path = OUT / CATEGORY_DIR[JOAO] / "index.html"
    if not old_path.exists():
        raise RuntimeError("Coleção histórica de João Cabral não encontrada")
    collection = read(new_path) if new_path.exists() else read(legacy_source)
    old_card = read(legacy_source).select_one("main .post-card")
    if not collection.find("a", href=f"../{OLD_POST}"):
        first = collection.select_one("main .post-card")
        if first:
            first.insert_before(old_card)
        else:
            collection.select_one("main .content").append(old_card)
    collection.title.string = f"{JOAO} — AfinidadeSeletivas"
    collection.select_one(".page-title").string = JOAO
    deck = collection.select_one(".page-deck")
    deck.clear()
    deck.append("Poemas de João Cabral de Melo Neto selecionados no blog. ")
    count = collection.new_tag("span", attrs={"class": "small"})
    count.string = f"{len(collection.select('main .post-card'))} texto(s) no acervo."
    deck.append(count)
    description = collection.find("meta", attrs={"name": "description"})
    if description:
        description["content"] = "Poemas de João Cabral de Melo Neto selecionados no blog."
    write(new_path, collection)

    # O endereço da antiga categoria continua recebendo seus visitantes.
    old_path.write_text(
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url=../afins_joao_cabral_de_melo_neto/index.html">'
        '<link rel="canonical" href="https://afinidadeseletivas.com/afins_joao_cabral_de_melo_neto/">'
        '<title>João Cabral de Melo Neto — AfinidadeSeletivas</title></head><body>'
        '<p>A coleção está em <a href="../afins_joao_cabral_de_melo_neto/index.html">'
        'João Cabral de Melo Neto</a>.</p></body></html>',
        encoding="utf-8",
    )

    page = OUT / OLD_POST
    soup = read(page)
    soup.body["class"] = [
        f"poem-{CATEGORY_DIR[JOAO]}" if c == "poem-poemas_da_cabra" else c
        for c in soup.body.get("class", [])
    ]
    for a in (soup.select_one(".posted a"), soup.select_one(".post-navigation .category a")):
        if a:
            a.string = JOAO
            a["href"] = f"../../../../{CATEGORY_DIR[JOAO]}/index.html"
    context = soup.select_one(".post-context")
    if context:
        context.string = context.get_text().replace(OLD_CATEGORY, JOAO, 1)
    write(page, soup)

    archive_path = OUT / "arquivo" / "index.html"
    archive = read(archive_path)
    link = archive.find("a", href=f"../{OLD_POST}")
    if not link:
        raise RuntimeError("Poema da Cabra não encontrado no arquivo cronológico")
    label = link.find_parent("li").find("span", class_="small")
    label.string = f"[{JOAO}]"
    write(archive_path, archive)


def make_authors_index() -> list[tuple[str, str, int]]:
    authors = []
    for category, directory in [("Afins_Ferreira Gullar", CATEGORY_DIR["Afins_Ferreira Gullar"]), *AFINS_AUTHOR_SLUGS.items()]:
        path = OUT / directory / "index.html"
        if not path.exists():
            continue
        count = len(read(path).select("main .post-card"))
        if count:
            authors.append((category.removeprefix("Afins_"), directory, count))
    authors.sort(key=lambda a: author_key(a[0]))

    soup = read(OUT / "poetasafins" / "index.html")
    soup.title.string = "Autores — AfinidadeSeletivas"
    desc = soup.find("meta", attrs={"name": "description"})
    if desc:
        desc["content"] = "Índice alfabético das coleções de poetas do AfinidadeSeletivas."
    content = soup.select_one("main .content")
    content.clear()
    h2 = soup.new_tag("h2", attrs={"class": "page-title"})
    h2.string = "Autores"
    content.append(h2)
    p = soup.new_tag("p", attrs={"class": "page-deck"})
    p.append("Coleções de poetas reunidas no blog. ")
    small = soup.new_tag("span", attrs={"class": "small"})
    small.string = f"{len(authors)} autores."
    p.append(small)
    content.append(p)
    ul = soup.new_tag("ul", attrs={"class": "authors-list"})
    for name, directory, count in authors:
        li = soup.new_tag("li")
        a = soup.new_tag("a", href=f"../{directory}/index.html")
        a.string = name
        li.append(a)
        small = soup.new_tag("span", attrs={"class": "small"})
        small.string = f"{count} texto{'s' if count != 1 else ''}"
        li.append(small)
        ul.append(li)
    content.append(ul)
    write(OUT / "autores" / "index.html", soup)
    return authors


def link_poetas_afins() -> None:
    path = OUT / "poetasafins" / "index.html"
    soup = read(path)
    deck = soup.select_one(".page-deck")
    if deck:
        deck.insert(0, "Poemas de diferentes autores reunidos no acervo. ")
        # Remove a antiga frase, mantendo o contador atualizado pelo gerador.
        for node in list(deck.contents):
            if isinstance(node, str) and "Poemas e vozes de autores" in node:
                node.replace_with("")
        callout = soup.new_tag("p", attrs={"class": "authors-link"})
        callout.append("Procura um poeta? Consulte o ")
        a = soup.new_tag("a", href="../autores/index.html")
        a.string = "índice de autores"
        callout.append(a)
        callout.append(" e suas coleções.")
        deck.insert_after(callout)
    write(path, soup)


def simplify_navigation(authors: list[tuple[str, str, int]]) -> None:
    visible = {c for c in CATEGORY_DIR if not c.startswith("Afins_") and c != OLD_CATEGORY}
    for path in OUT.rglob("*.html"):
        soup = read(path)
        changed = False
        for box in soup.select(".rightbar .box"):
            heading = box.find("h2")
            if not heading or heading.get_text(" ", strip=True) != "Categorias":
                continue
            ul = box.find("ul")
            if not ul:
                continue
            for li in list(ul.find_all("li", recursive=False)):
                a = li.find("a")
                if a and a.get_text(" ", strip=True) not in visible:
                    li.decompose()
                    changed = True
            poet = next((li for li in ul.find_all("li", recursive=False) if li.find("a") and li.find("a").get_text(" ", strip=True) == "PoetasAfins"), None)
            if poet:
                li = soup.new_tag("li")
                prefix = os.path.relpath(OUT, path.parent).replace("\\", "/")
                prefix = "" if prefix == "." else prefix + "/"
                a = soup.new_tag("a", href=f"{prefix}autores/index.html")
                a.string = "Autores"
                li.append(a)
                small = soup.new_tag("span", attrs={"class": "small"})
                small.string = f" ({len(authors)})"
                li.append(small)
                poet.insert_after(li)
                changed = True

        if path == OUT / "index.html":
            holder = soup.select_one(".reading-paths")
            if holder:
                for card in list(holder.select(".reading-path")):
                    a = card.find("a")
                    if a and (a.get_text(" ", strip=True) == OLD_CATEGORY or a.get_text(" ", strip=True).startswith("Afins_")):
                        card.decompose()
                        changed = True
                poet = next((card for card in holder.select(".reading-path") if card.find("a") and card.find("a").get_text(" ", strip=True) == "PoetasAfins"), None)
                if poet:
                    card = soup.new_tag("div", attrs={"class": "reading-path"})
                    h3 = soup.new_tag("h3")
                    a = soup.new_tag("a", href="autores/index.html")
                    a.string = "Autores"
                    h3.append(a)
                    h3.append(" ")
                    small = soup.new_tag("span", attrs={"class": "small"})
                    small.string = f"({len(authors)})"
                    h3.append(small)
                    card.append(h3)
                    p = soup.new_tag("p")
                    p.string = "Encontre as coleções de poetas pelo nome."
                    card.append(p)
                    poet.insert_after(card)
                    changed = True
        if changed:
            write(path, soup)


def organize_poets() -> None:
    migrate_joao()
    authors = make_authors_index()
    link_poetas_afins()
    simplify_navigation(authors)
    generate_sitemap()

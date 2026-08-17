from __future__ import annotations

import os
import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"

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


def soup_file(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def write_soup(path: Path, soup: BeautifulSoup) -> None:
    path.write_text(str(soup), encoding="utf-8")


def change_deck_count(soup: BeautifulSoup, delta: int) -> None:
    small = soup.select_one(".page-deck .small")
    if not small:
        return
    text = small.get_text(" ", strip=True)
    m = re.search(r"\d+", text)
    if m:
        small.string = text[:m.start()] + str(int(m.group()) + delta) + text[m.end():]


def reclassify_provocacao() -> None:
    rel = "archive/2006/10/26/provocacao-para-heloisa-helena.html"
    page = OUT / rel
    if not page.exists():
        raise RuntimeError(f"Página histórica não encontrada: {rel}")

    soup = soup_file(page)
    body = soup.body
    classes = list(body.get("class") or [])
    classes = ["prose-conto" if c == "prose-tese" else c for c in classes]
    if "prose-conto" not in classes:
        classes.append("prose-conto")
    body["class"] = classes

    posted = soup.select_one(".posted a")
    if posted:
        posted.string = "Conto"
        posted["href"] = "../../../../conto/index.html"
    cat = soup.select_one(".post-navigation .category a")
    if cat:
        cat.string = "Conto"
        cat["href"] = "../../../../conto/index.html"
    write_soup(page, soup)

    # Corrige a categoria exibida no arquivo cronológico.
    archive_path = OUT / "arquivo" / "index.html"
    arc = soup_file(archive_path)
    link = arc.find("a", href="../" + rel)
    if link:
        li = link.find_parent("li")
        label = li.find("span", class_="small") if li else None
        if label:
            label.string = "[Conto]"
    write_soup(archive_path, arc)

    # Move o cartão histórico de Tese para Conto.
    tese_path = OUT / "tese" / "index.html"
    conto_path = OUT / "conto" / "index.html"
    tese = soup_file(tese_path)
    conto = soup_file(conto_path)
    old_link = tese.find("a", href="../" + rel)
    card = old_link.find_parent("article", class_="post-card") if old_link else None
    already = conto.find("a", href="../" + rel)
    if card and not already:
        card_html = str(card)
        card.decompose()
        dest_card = BeautifulSoup(card_html, "html.parser").find("article")
        content = conto.select_one("main .content")
        first = content.find("article", class_="post-card", recursive=False) if content else None
        if first:
            first.insert_before(dest_card)
        elif content:
            content.append(dest_card)
        change_deck_count(tese, -1)
        change_deck_count(conto, +1)
    write_soup(tese_path, tese)
    write_soup(conto_path, conto)


def rebuild_category_sidebar_counts() -> None:
    counts = {c: 0 for c in CATEGORY_DIR}
    for path in (OUT / "archive").glob("[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]/*.html"):
        soup = soup_file(path)
        a = soup.select_one(".post-navigation .category a")
        if not a:
            a = soup.select_one(".posted a")
        category = a.get_text(" ", strip=True) if a else ""
        if category in counts:
            counts[category] += 1

    for path in OUT.rglob("*.html"):
        soup = soup_file(path)
        changed = False
        for box in soup.select(".rightbar .box"):
            h = box.find("h2")
            if not h or h.get_text(" ", strip=True) != "Categorias":
                continue
            for li in box.select("ul > li"):
                a = li.find("a")
                span = li.find("span", class_="small")
                name = a.get_text(" ", strip=True) if a else ""
                if span and name in counts:
                    span.string = f"({counts[name]})"
                    changed = True
        if path == OUT / "index.html":
            for card in soup.select(".reading-path"):
                a = card.find("a")
                span = card.find("span", class_="small")
                name = a.get_text(" ", strip=True) if a else ""
                if span and name in counts:
                    span.string = f"({counts[name]})"
                    changed = True
        if changed:
            write_soup(path, soup)


def expand_emmanuel() -> None:
    path = OUT / "archive" / "2007" / "06" / "01" / "emmanuel-e-a-literatura-evangelica.html"
    if not path.exists():
        raise RuntimeError("Página histórica de Emmanuel não encontrada")
    soup = soup_file(path)
    article = soup.select_one("article.post-body")
    if not article:
        raise RuntimeError("Corpo do post de Emmanuel não encontrado")

    text = article.get_text("\n", strip=True)
    nab = re.search(r'(["“]Um naufrágio.*?\(Lolita de Vladimir Nabokov\)\.)', text, flags=re.S)
    ave = re.search(r'(["“]Deslumbrante caminho.*?\(Ave, Cristo de Emmanuel\)\.)', text, flags=re.S)
    if not nab or not ave:
        raise RuntimeError("Não foi possível preservar as duas citações históricas de Emmanuel")

    lead_image = article.select_one(".prose-lead-image")
    ave_link = article.find("a", href=re.compile(r"ave_cristo", re.I))
    lead_html = str(lead_image) if lead_image else ""
    ave_html = str(ave_link) if ave_link else ""

    revised = [
        "O que faz deste texto uma obra de arte? O uso das metáforas (palácio intelectual, folha de parreira); as imagens ( um naufrágio, uma estátua); os adjetivos (tiritante, trêmulo); a intensidades dos sentimentos (eu me dissolvi ao sol)? Sim, tudo isso junto. Todos os recursos estilísticos nas mãos de um ‘artífice’ são capazes de produzir o Belo – esse conceito vago e permeável, pouco científico, mas, por enquanto, necessário.",
        "Qualquer um, minimamente educado em artes, saberá reconhecer a beleza de um texto como este de Nabokov. Alguns conseguirão ver, além do erótico, o apelo estético da narrativa. Sentirão a poesia das palavras. Estes raros compreenderão o conceito de Belo. O autor, por outro lado, pensava em algo além do prazer estético: provavelmente queria falar do Erótico, da carnalidade do mundo. Em outras palavras, sua arte tinha um alvo preciso: o homem comum, com suas inquietações mercurianas. Por isso, nada de humano lhe é estranho; a narrativa prossegue no enredamento da vida cotidiana. Tudo ali é vida comum, nada alcança de sublime. Mesmo assim, a narrativa não é pobre, pois o ‘artífice’ lhe modelou as letras. Ou seja, o mesmo tema nas mãos de um artista sem talento se tornaria literatura erótica. Esse ‘plus’ é encontrado, exatamente, no manejamento dos recursos estilísticos. São as imagens e os adjetivos, empregados com precisão, que garantem a força das ironias, dos cinismos, do desespero e da intensidade da tensão sexual do texto.",
        "O autor foi buscar esses recursos no mundo, onde grassam as escolas literárias e as vaidades momentâneas de cada grupo. Ele precisava falar a língua do mundo para ser entendido pelo mundo. É por essa razão que toda a sua narrativa segue uma orientação secular: o tema, a linguagem, a estrutura, o ambiente, etc., tudo fala do mundo e de coisas do mundo.",
        "Os que são acostumados com o mundo (e não são poucos...) reconhecem a beleza do romance e, dificilmente, conseguirão identificar a beleza de outros textos que não apresentem esses ‘recursos’.",
        "É por isso que os minimamente educados em artes recebem com estranheza os romances de Emmanuel, o autor espiritual que escreveu através dos dedos de Chico Xavier... Não se sabe se Emmanuel é um heterônimo ou, de fato, uma entidade: este detalhe permanecerá por algum tempo sem solução. Por ora, restou os cinco romances de sua autoria (além de algumas centenas de outros livros, evidentemente doutrinários), que, com respeito a todos os cânones da literatura nacional, deveriam, pelo menos, ser tratados com mais respeito pelo meio acadêmico das Universidades, pela “Academia”.",
        "Os romances “Há dois mil anos”, ‘50 anos depois” e “Ave, Cristo” contam a saga autobiográfica do autor através de sucessivas reencarnações. É ainda a veia narcisista do escritor que quer falar de si, mas é também a sinceridade de uma preocupação evangélica, indisfarçável a cada linha.",
        "Não se encontrará nesses romances os artifícios literários da literatura comum e, talvez, por isso, eles não tenham sido apreciados com a devida seriedade. A “Academia”, além de afastar, peremptória, o tema constrangedor da ‘reencarnação’, prefere olhar o próprio umbigo e estudar o cânone que ela mesma escolheu...",
        "A trilogia, no entanto, é obra de arte, mesmo vista com o monóculo da ciência literária. Não há erro de estrutura: todas as narrativas são perfeitas, não sobrando uma trama, não faltando um personagem; não há erro de linguagem: todas as narrativas são coerentemente evangélicas, nenhuma palavra profana, nenhum sintagma indeterminado, cada personagem com sua peculiaridade linguística, o vocábulo de latinista; não há erro de historicidade: todas as informações podem ser rastreadas, desde a cartografia do Império Romano, até a etiologia das pequenas cidades da Itália, passando pelo nome dos Césares e das ‘vias’ da capital.",
        "Emmanuel produz uma literatura evangélica no sentido mais puro possível. Certo, que se sente falta do ardor estético que se esta acostumado: a intensidade erótico-linguística de Nabokov; a inteligência irônica de Machado de Assis; a raiva de Maiakoviski; o lirismo latino de Neruda ou a melancolia de Nauro Machado. Mas, convenha-se, Emmanuel não pode pregar o Evangelho com a mesma pena das dores humanas. Literatura evangélica é exatamente depurar-se dos excessos humanos: dizer a verdade do Amor para construir a edificação do mundo. Daí a necessidade de chorar! As lágrimas, para quem as sabe alcançar na leitura dessas obras, são também uma forma de angelizar-se. E o alvo foi atingido.",
        "A Academia precisa aprender a reconhecer na ‘boa’ literatura evangélica as mesmas qualidades literárias da literatura secular. O paradigma da ‘espiritualidade’ pode ser tão válido quanto o da ‘lubricitate’. O homem é um ser total, talvez, como dizia Nietzsche, uma corda atada entre o animal e o além do homem:",
    ]
    expansion = [
        "Todos fomos feitos para brilhar. A ascensão é o caminho de todo ser: do verme à estrela. O homem, entre todos, tem o privilégio de se conduzir à luz voluntariamente e, com isso, atingi-la com mais diligência. A semente, se ativada, alcança a árvore. O homem, porém, é sempre ativado, mas poucos deixam de ser homens. Poucos viram passarinho.",
        "Somos feitos para a grandeza. Importa saber qual! O que, aparentemente, representa um fracasso para uns, pode significar uma grande vitória para quem a vivenciou. As existências mais simples possuem suas grandezas particulares, tanto quanto os heroísmos mais patéticos. Aliás, não é com mansões em Hollywood que se identificam os grandes homens. Há muitos ratos em palácios suntuosos.",
        "Mário Ferreira dos Santos, um velho filósofo que só consegui conhecer recentemente, graças à Internet, parece ser um desses que abriu sua própria luz. Eu imagino todo o esforço que lhe foi exigido para realizar seus estudos e aprender a linguagem filosófica; quantos erros, quantas insônias, quantas ilusões superadas para afirma sua vontade de potência intelectual.",
        "Não estou afirmando que só as fábricas de poesia e filosofia são capazes de produzir passarinhos. As indústrias têxteis também. Tenho certeza que José de Alencar tem luz própria. Tenho certeza que Pedro Simon tem luz própria. Tenho certeza que seu Olegário,vaqueiro em Arari, alcançou luz própria na respiração dos alagados e dos bois da baixada maranhense. Qualquer tarefa é oportunidade para brilhar.",
        "Num mundo cheio de sombras - “ trevas que nascem da ignorância, da maldade, da insensatez, envolvendo povos, instituições e pessoas” - num mundo de ódios abissais  é urgente acendermos alguma luz. E fazer luz não é ofuscar, não é atrair as atenções para si. É antes de tudo, emitir raios de claridade sobre as coisas. É afastar a penumbra do caminho dos homens: onde houver ignorância que se leve o saber; onde houver maldade que se leve a justiça; onde houver insensatez que se leve a luz... da razão.",
    ]

    article.clear()
    if lead_html:
        node = BeautifulSoup(lead_html, "html.parser").find()
        if node:
            article.append(node)
    q1 = soup.new_tag("blockquote"); q1.string = nab.group(1); article.append(q1)
    for txt in revised:
        p = soup.new_tag("p"); p.string = txt; article.append(p)
    if ave_html:
        node = BeautifulSoup(ave_html, "html.parser").find()
        if node:
            article.append(node)
    q2 = soup.new_tag("blockquote"); q2.string = ave.group(1); article.append(q2)
    h = soup.new_tag("h4"); h.string = "Gente é Pra Brilhar"; article.append(h)
    bible = soup.new_tag("p"); bible.string = "“Assim resplandeça a vossa luz diante dos homens” Jesus (Mateus, 5:16.)"; article.append(bible)
    for txt in expansion:
        p = soup.new_tag("p"); p.string = txt; article.append(p)

    write_soup(path, soup)


def main() -> int:
    if not OUT.exists():
        raise SystemExit("ERRO: _site não existe. Execute tools/build_site.py primeiro.")
    reclassify_provocacao()
    expand_emmanuel()
    rebuild_category_sidebar_counts()
    print("Decisões editoriais aplicadas: Provocação→Conto; Emmanuel revisado/ampliado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Novas publicações — AfinidadeSeletivas

Esta infraestrutura foi criada para acrescentar textos novos sem reescrever o acervo de 2006–2007 e sem Jekyll.

## Ideia geral

1. Um texto novo nasce como arquivo Markdown em `content/posts/`.
2. O gerador lê título, data, categoria, tags e tipo do texto.
3. Ele copia o site histórico para uma pasta de saída `_site/`.
4. Sobre essa cópia, cria a nova página e atualiza os índices necessários.
5. O acervo-fonte continua intocado.

## Formato do arquivo

Use `content/MODELO_DE_POST.md` como molde.

As categorias aceitas são:

- BlogsFeras
- Conto
- Crônica
- Humor
- Musica
- PoesiasEletivas
- PoetasAfins
- Afins_Ferreira Gullar
- Afins_Carlos Drummond de Andrade, Afins_César Vallejo, Afins_Dylan Thomas
- Afins_E. E. Cummings, Afins_Edmond Jabès, Afins_Eugenio Montale, Afins_Ezra Pound
- Afins_Federico García Lorca, Afins_Fernando Pessoa, Afins_Francis Ponge
- Afins_Georg Trakl, Afins_Herberto Helder, Afins_Jacques Roubaud, Afins_José Lezama Lima
- Afins_João Cabral de Melo Neto
- Afins_Laura Riding, Afins_Lawrence Ferlinghetti, Afins_Marina Tsvetaeva, Afins_Octavio Paz
- Afins_Paul Celan, Afins_Paul Valéry, Afins_Paul Van Ostaijen
- Afins_Rainer Maria Rilke, Afins_Robert Creeley, Afins_Sebastião Alba, Afins_Sylvia Plath
- Afins_T. S. Eliot, Afins_Vasko Popa, Afins_Velimir Khlebnikov, Afins_Vladimir Maiakóvski
- Afins_Wallace Stevens, Afins_William Butler Yeats, Afins_William Carlos Williams, Afins_Yves Bonnefoy
- Projeto
- Tese

`kind` pode ser `prose` ou `poetry`.

## Coleções de poetas

Cada poeta pode ter uma coleção própria no formato `Afins_Nome do Poeta`. O índice público fica em `autores/index.html` e reúne as coleções disponíveis. Os poemas novos ficam em arquivos Markdown independentes dentro de `content/posts/`; o nome do autor também integra o `slug`, evitando colisões entre poemas homônimos. A antiga categoria `Poemas da Cabra` é mantida apenas como endereço histórico de entrada para a coleção de João Cabral.

Para criar uma categoria de outro poeta, acrescente seu nome e diretório ao dicionário `AFINS_AUTHOR_SLUGS`, em `tools/build_site.py`, e use essa categoria no cabeçalho dos poemas.

O workflow monta e valida o site em pull requests. A publicação no GitHub Pages ocorre somente depois que as alterações chegam à branch `main`.

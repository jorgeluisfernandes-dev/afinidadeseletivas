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
- Poemas da Cabra
- PoesiasEletivas
- PoetasAfins
- Projeto
- Tese

`kind` pode ser `prose` ou `poetry`.

## Neste momento

Não existe nenhum texto novo em `content/posts/`. Portanto esta branch contém somente a oficina de publicação, sem nova postagem.

O workflow `validar-infra.yml` apenas monta e valida uma cópia do site. Ele NÃO publica no GitHub Pages.

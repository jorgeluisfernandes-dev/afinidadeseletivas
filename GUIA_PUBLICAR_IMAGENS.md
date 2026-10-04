# Publicar imagens no AfinidadeSeletivas

## Com ajuda do ChatGPT

Anexe a imagem pronta e envie:

> Publique esta imagem no afinidadeseletivas.com, em PoesiasEletivas. Preserve a imagem inteira, sem cortes e sem título visível acima dela. Nota abaixo: “[sua nota]”. Use uma identificação simples nos índices. Autorizo a publicação. Confira a página e devolva o link.

Se a composição já estiver aprovada, indique “Use a última imagem aprovada desta conversa”.

## Pelo GitHub, sem ChatGPT

1. Abra o repositório jorgeluisfernandes-dev/afinidadeseletivas.
2. Em assets/poemas-visuais, use Add file → Upload files para enviar a imagem com nome simples, sem espaços nem acentos.
3. Em content/posts, use Add file → Create new file e crie AAAA-MM-DD-identificacao.md.
4. Copie o modelo abaixo, substitua os dados e use a mesma data no nome e no cabeçalho.
5. Confirme as alterações na branch main. A publicação é automática; acompanhe a aba Actions até o fluxo terminar com sucesso.
6. Abra a página em /archive/AAAA/MM/DD/identificacao.html e confira a imagem e a nota.

```markdown
+++
title = "Identificação para os índices"
slug = "identificacao"
date = "2026-10-04"
category = "PoesiasEletivas"
tags = ["poesia visual"]
kind = "prose"
summary = "Nota breve sobre a obra."
+++

<style>
.content .post-title { display: none; }
.poema-visual { margin: 1.5rem 0; }
.poema-visual img { display: block; width: 100%; height: auto; }
.poema-visual figcaption { margin-top: 1rem; font-size: 1rem; line-height: 1.6; }
</style>

<figure class="poema-visual">
<a href="../../../../assets/poemas-visuais/imagem.webp"><img src="../../../../assets/poemas-visuais/imagem.webp" alt="Descrição breve da imagem e texto do poema." /></a>
<figcaption>Sua nota abaixo da imagem.</figcaption>
</figure>
```

Use a extensão real do arquivo (.jpg, .png ou .webp) nos dois endereços. A identificação aparece nos índices; a obra permanece sem título visível. O campo alt permite que leitores de tela acessem o conteúdo.

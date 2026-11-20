# Estatísticas e verificação do Afinidades Eletivas

O site usa **Cloudflare Web Analytics** e **Google Analytics 4 (GA4)**, com identificador público de medição `G-RPTB8H6JGP`. Durante a publicação no GitHub Pages,
`tools/inject_cloudflare_analytics.py` instala o beacon nas páginas HTML.
`tools/inject_google_analytics.py` instala o Google Analytics no `<head>`;`tools/validate_analytics.py` verifica automaticamente se cada página HTML
com fechamento `</body>` recebeu **uma vez cada serviço**, evitando ausência
acidental ou duplicação da coleta. A página de verificação do Google, que não
contém corpo HTML, é excluída desse requisito.

## Consultar as visitas (sem programação)

1. Entre na sua conta em https://dash.cloudflare.com/.
2. Abra **Web Analytics** e selecione o site **afinidadeseletivas.com**.
3. Escolha o intervalo de datas disponível.
4. Compare **Visitors** (visitantes), **Page views** (visualizações) e
   **Visits** (visitas ou sessões) quando essas métricas estiverem disponíveis.
5. Na lista de páginas, compare os caminhos dos artigos mais lidos.

O painel é **privado**, e o acesso ao repositório GitHub não libera os dados
da conta Cloudflare. Não publique tokens privados, chaves de API nem
capturas que exponham credenciais em arquivos do site.

### Por que não somar os números dos artigos?

Uma pessoa pode abrir vários textos e retornar em outra sessão. Somar
visualizações não revela quantos **visitantes únicos** existiram. O histórico
disponível depende da data de ativação e da retenção do serviço. Dados
anteriores à instalação do medidor não são recuperados automaticamente.

### O que os testes automáticos conseguem verificar?

* O beacon foi adicionado uma única vez por página HTML.
* As páginas e os links locais passaram pela validação do GitHub Actions.
* A publicação automática ocorreu sem falhas.

Eles **não provam** que as solicitações chegaram ao painel da Cloudflare:
isso exige consulta ao painel e teste em um navegador real, com bloqueadores
de rastreamento desativados durante o teste. Alguns visitantes bloqueiam
ferramentas de análise, portanto nenhuma medição representa necessariamente
100% das pessoas reais.

### Teste simples após publicar

Abra uma página do blog no navegador, procure `beacon.min.js` na aba
**Rede / Network** das ferramentas do desenvolvedor e confira o painel
depois. Não confunda visitas de teste com leitores reais.

## Histórico desde a fundação

Para reconstruir a audiência antiga, procure eventuais exportações do
Blogger/WordPress, ferramentas de estatística anteriores ou registros da
hospedagem antiga. Períodos com métricas diferentes devem ser apresentados
separadamente; nunca some visitantes únicos de períodos diferentes como se
representassem pessoas distintas.

## Publicação e diagnóstico

No repositório, abra **Actions → Publicar AfinidadeSeletivas**. A execução
`build` monta as páginas, uniformiza os rótulos de categoria, instala e
valida o analytics, verifica links e só depois permite a publicação.

As categorias visíveis padronizadas são **Projetos** e **Ensaios**. Os
endereços históricos `/projeto/` e `/tese/` permanecem os mesmos, assim
como os endereços originais dos artigos.

## Google Analytics 4 (GA4)

1. Abra https://analytics.google.com/ e selecione a propriedade do Afinidades.
2. Entre em **Relatórios → Tempo real** e visite https://afinidadeseletivas.com/ numa janela de navegador sem bloqueador de rastreamento (somente para este teste).
3. Verifique se aparece pelo menos uma visualização. Pode haver atraso no recebimento.
4. Para conferir a instalação, abra o código-fonte da página e procure `G-RPTB8H6JGP` — deve aparecer no carregamento do `gtag.js` e na chamada de configuração.
5. Em **Relatórios → Engajamento → Páginas e telas**, examine os textos mais lidos depois que houver dados.

O GA4 não reconstrói visitas anteriores à instalação. Os números de GA4 e Cloudflare podem diferir porque a metodologia de coleta, bloqueadores e definições de métricas não são idênticos. Não some os totais das duas ferramentas.

**Privacidade:** avalie as obrigações de informação e consentimento previstas na LGPD antes de usar ferramentas de rastreamento em produção, e ajuste eventuais avisos de privacidade/consentimento conforme sua configuração. O ID `G-` é público; nunca publique acessos à conta ou chaves privadas.

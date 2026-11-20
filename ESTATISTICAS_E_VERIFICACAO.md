# Estatísticas e verificação do Afinidades Eletivas

O site usa **Cloudflare Web Analytics**. Durante a publicação no GitHub Pages,
`tools/inject_cloudflare_analytics.py` instala o beacon nas páginas HTML.
`tools/validate_analytics.py` verifica automaticamente se cada página HTML
com fechamento `</body>` recebeu o beacon **uma vez**, evitando ausência
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

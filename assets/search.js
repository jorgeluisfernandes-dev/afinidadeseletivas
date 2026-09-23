(function () {
  const form = document.querySelector('.search-form');
  if (!form) return;
  const input = document.getElementById('query');
  const status = document.getElementById('search-status');
  const results = document.getElementById('search-results');
  const normalize = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  let index;

  function show(items, query) {
    results.replaceChildren();
    if (query.length < 2) {
      status.textContent = 'Digite ao menos duas letras para começar.';
      return;
    }
    status.textContent = `${items.length} texto${items.length === 1 ? '' : 's'} encontrado${items.length === 1 ? '' : 's'}.`;
    for (const item of items.slice(0, 40)) {
      const article = document.createElement('article');
      article.className = 'post-card';
      const meta = document.createElement('div');
      meta.className = 'meta';
      meta.textContent = `${item.date} — ${item.category}`;
      const h3 = document.createElement('h3');
      const link = document.createElement('a');
      link.href = item.url;
      link.textContent = item.title;
      h3.append(link);
      const p = document.createElement('p');
      p.textContent = item.summary;
      article.append(meta, h3, p);
      results.append(article);
    }
    if (items.length > 40) status.textContent += ' Exibindo os primeiros 40; refine a busca.';
  }

  async function search() {
    const query = normalize(input.value.trim());
    if (query.length < 2) return show([], query);
    status.textContent = 'Buscando…';
    try {
      if (!index) {
        const response = await fetch('indice.json');
        if (!response.ok) throw new Error('Falha ao carregar o índice');
        index = (await response.json()).map(item => ({
          ...item,
          searchable: normalize([item.title, item.summary, item.category, ...item.tags].join(' ')),
          titleKey: normalize(item.title),
        }));
      }
      const terms = query.split(/\s+/).filter(Boolean);
      const matches = index.filter(item => terms.every(term => item.searchable.includes(term)));
      const dateKey = item => item.date.split('/').reverse().join('');
      matches.sort((a, b) => Number(b.titleKey.includes(query)) - Number(a.titleKey.includes(query)) || dateKey(b).localeCompare(dateKey(a)));
      show(matches, query);
    } catch (error) {
      status.textContent = 'Não foi possível carregar a busca. Tente novamente.';
      results.replaceChildren();
    }
  }

  form.addEventListener('submit', event => { event.preventDefault(); search(); });
  const initial = new URLSearchParams(location.search).get('q');
  if (initial) { input.value = initial; search(); }
})();

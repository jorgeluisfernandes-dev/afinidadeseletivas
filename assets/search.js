(function () {
  const form = document.querySelector('.search-form');
  if (!form) return;
  const input = document.getElementById('query');
  const status = document.getElementById('search-status');
  const results = document.getElementById('search-results');
  const normalize = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const PER_PAGE = 20;
  let index = null;
  let matches = [];
  let displayed = 0;

  function snippet(item, terms) {
    const text = String(item.text || item.summary || '');
    const folded = normalize(text);
    let first = -1;
    for (const term of terms) {
      const at = folded.indexOf(term);
      if (at !== -1 && (first === -1 || at < first)) first = at;
    }
    if (first === -1) return item.summary || text.slice(0, 180);
    const start = Math.max(0, first - 75);
    const end = Math.min(text.length, first + 140);
    const prefix = start ? '…' : '';
    const suffix = end < text.length ? '…' : '';
    return prefix + text.slice(start, end).trim() + suffix;
  }

  function appendResults() {
    const batch = matches.slice(displayed, displayed + PER_PAGE);
    const terms = normalize(input.value.trim()).split(/\s+/).filter(Boolean);
    for (const item of batch) {
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
      p.textContent = snippet(item, terms);
      article.append(meta, h3, p);
      results.append(article);
    }
    displayed += batch.length;
    document.getElementById('search-more')?.remove();
    if (displayed < matches.length) {
      const button = document.createElement('button');
      button.id = 'search-more';
      button.type = 'button';
      button.textContent = `Mostrar mais resultados (${matches.length - displayed} restantes)`;
      button.addEventListener('click', appendResults);
      results.after(button);
    }
    status.textContent = `${matches.length} texto${matches.length === 1 ? '' : 's'} encontrado${matches.length === 1 ? '' : 's'}. Exibindo ${displayed}.`;
  }

  function score(item, terms, fullQuery) {
    const title = normalize(item.title);
    const tags = normalize((item.tags || []).join(' '));
    const category = normalize(item.category);
    const summary = normalize(item.summary);
    const body = normalize(item.text);
    const searchable = [title, tags, category, summary, body].join(' ');
    if (!terms.every(term => searchable.includes(term))) return -1;
    let points = title.includes(fullQuery) ? 25 : 0;
    for (const term of terms) {
      if (title.includes(term)) points += 12;
      if (tags.includes(term)) points += 8;
      if (category.includes(term)) points += 4;
      if (summary.includes(term)) points += 3;
      if (body.includes(term)) points += 1;
    }
    return points;
  }

  async function search() {
    const raw = input.value.trim();
    const query = normalize(raw);
    results.replaceChildren();
    document.getElementById('search-more')?.remove();
    displayed = 0;
    if (query.length < 2) {
      status.textContent = 'Digite ao menos duas letras para começar.';
      return;
    }
    status.textContent = 'Buscando…';
    try {
      if (!index) {
        const response = await fetch('indice.json');
        if (!response.ok) throw new Error('Indice indisponivel');
        index = await response.json();
      }
      const terms = query.split(/\s+/).filter(Boolean);
      matches = index.map(item => ({...item, rank: score(item, terms, query)}))
        .filter(item => item.rank >= 0)
        .sort((a, b) => b.rank - a.rank ||
          b.date.split('/').reverse().join('').localeCompare(a.date.split('/').reverse().join('')) ||
          a.title.localeCompare(b.title, 'pt-BR'));
      if (!matches.length) {
        status.textContent = 'Nenhum texto encontrado. Experimente outra palavra ou menos termos.';
        return;
      }
      appendResults();
      history.replaceState(null, '', '?q=' + encodeURIComponent(raw));
    } catch (error) {
      status.textContent = 'Não foi possível carregar a busca. Tente novamente.';
    }
  }

  form.addEventListener('submit', event => { event.preventDefault(); search(); });
  const initial = new URLSearchParams(location.search).get('q');
  if (initial) { input.value = initial; search(); }
})();
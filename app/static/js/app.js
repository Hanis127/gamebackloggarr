/* ── Modal ── */
const overlay = document.getElementById('modalOverlay');
const modalClose = document.getElementById('modalClose');
const addGameBtn = document.getElementById('addGameBtn');
const addGameBtn2 = document.getElementById('addGameBtn2');

function openModal() { overlay.classList.add('open'); searchInput.focus(); }
function closeModal() {
  overlay.classList.remove('open');
  searchInput.value = '';
  searchResults.classList.add('hidden');
  searchResults.innerHTML = '';
  addForm.classList.add('hidden');
}

addGameBtn?.addEventListener('click', openModal);
addGameBtn2?.addEventListener('click', openModal);
modalClose?.addEventListener('click', closeModal);
overlay?.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

/* ── IGDB search ── */
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
const addForm = document.getElementById('addForm');

let searchTimeout;
searchInput?.addEventListener('input', () => {
  clearTimeout(searchTimeout);
  const q = searchInput.value.trim();
  if (q.length < 2) {
    searchResults.classList.add('hidden');
    return;
  }
  searchTimeout = setTimeout(() => doSearch(q), 350);
});

async function doSearch(q) {
  searchResults.classList.remove('hidden');
  searchResults.innerHTML = '<div class="search-loading">Searching IGDB…</div>';
  try {
    const resp = await fetch(`/api/igdb/search?q=${encodeURIComponent(q)}`);
    const games = await resp.json();
    if (!games.length) {
      searchResults.innerHTML = '<div class="search-empty">No results found</div>';
      return;
    }
    searchResults.innerHTML = games.map(g => `
      <div class="search-item" data-game='${JSON.stringify(g).replace(/'/g, "&#39;")}'>
        ${g.cover_url
          ? `<img src="${g.cover_url}" alt="${escHtml(g.title)}">`
          : `<div class="search-item-no-cover">🎮</div>`}
        <div class="search-item-info">
          <div class="search-item-title">${escHtml(g.title)}</div>
          <div class="search-item-meta">${[g.release_year, g.genres?.split(', ')[0]].filter(Boolean).join(' · ')}</div>
        </div>
      </div>
    `).join('');

    searchResults.querySelectorAll('.search-item').forEach(el => {
      el.addEventListener('click', () => selectGame(JSON.parse(el.dataset.game)));
    });
  } catch (e) {
    searchResults.innerHTML = '<div class="search-empty">Search failed — check IGDB credentials</div>';
  }
}

function selectGame(g) {
  document.getElementById('f_igdb_id').value = g.igdb_id;
  document.getElementById('f_title').value = g.title;
  document.getElementById('f_cover_url').value = g.cover_url || '';
  document.getElementById('f_summary').value = g.summary || '';
  document.getElementById('f_genres').value = g.genres || '';
  document.getElementById('f_platforms').value = g.platforms || '';
  document.getElementById('f_release_year').value = g.release_year || '';
  document.getElementById('f_rating').value = g.rating || '';

  document.getElementById('selectedGame').innerHTML = `
    ${g.cover_url ? `<img src="${g.cover_url}" alt="${escHtml(g.title)}">` : ''}
    <div class="selected-game-info">
      <div class="selected-game-title">${escHtml(g.title)}</div>
      <div class="selected-game-meta">
        ${[g.release_year, g.rating ? '★ ' + g.rating : null, g.genres?.split(', ')[0]].filter(Boolean).join(' · ')}
      </div>
      ${g.summary ? `<div class="selected-game-meta" style="margin-top:4px">${escHtml(g.summary.slice(0, 100))}…</div>` : ''}
    </div>
  `;

  searchResults.classList.add('hidden');
  addForm.classList.remove('hidden');
  searchInput.value = g.title;
}

/* ── Voting ── */
document.querySelectorAll('.vote-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const gameId = btn.dataset.game;
    const value = parseInt(btn.dataset.value);
    try {
      const resp = await fetch(`/games/${gameId}/vote/${value}`, { method: 'POST' });
      const data = await resp.json();

      const scoreEl = document.getElementById(`score-${gameId}`);
      if (scoreEl) scoreEl.textContent = data.score;

      const card = btn.closest('.game-card');
      card.querySelector('.upvote').classList.toggle('active', data.my_vote === 1);
      card.querySelector('.downvote').classList.toggle('active', data.my_vote === -1);
    } catch (e) {
      console.error('Vote failed', e);
    }
  });
});

/* ── Utils ── */
function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

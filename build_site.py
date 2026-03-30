"""
Build static site from crawled data.
Generates docs/index.html with embedded JSON data.
"""

import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")


def load_data(platform):
    path = os.path.join(DATA_DIR, f"{platform}.json")
    if not os.path.exists(path):
        return {"crawled_at": None, "total": 0, "queries": [], "items": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build():
    ebay = load_data("ebay")
    depop = load_data("depop")

    all_queries = sorted(set(ebay.get("queries", []) + depop.get("queries", [])))
    crawled_at = {
        "ebay": ebay.get("crawled_at", ""),
        "depop": depop.get("crawled_at", ""),
    }

    # Combine all items
    all_items = []
    for item in ebay.get("items", []):
        item["_platform"] = "ebay"
        all_items.append(item)
    for item in depop.get("items", []):
        item["_platform"] = "depop"
        all_items.append(item)

    # Embed data as JSON in HTML
    data_json = json.dumps({
        "items": all_items,
        "queries": all_queries,
        "crawled_at": crawled_at,
    }, ensure_ascii=False)

    html = generate_html(data_json)

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Built: docs/index.html")
    print(f"  eBay: {ebay['total']} items | Depop: {depop['total']} items")
    print(f"  Total: {len(all_items)} items")


def generate_html(data_json):
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vintage Finder - eBay & Depop</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>{CSS}</style>
</head>
<body>
    <header>
        <div class="header-inner">
            <h1>Vintage Finder</h1>
            <p class="subtitle">eBay & Depop - Daily Updated</p>
            <div class="crawl-info" id="crawlInfo"></div>
        </div>
    </header>
    <main>
        <section class="platform-tabs">
            <button class="platform-tab active" data-platform="all" onclick="setPlatform('all')"><span class="tab-label">ALL</span></button>
            <button class="platform-tab" data-platform="ebay" onclick="setPlatform('ebay')"><span class="tab-label">eBay</span></button>
            <button class="platform-tab" data-platform="depop" onclick="setPlatform('depop')"><span class="tab-label">Depop</span></button>
        </section>
        <section class="search-panel">
            <div class="search-row">
                <div class="search-input-wrap">
                    <input type="text" id="searchText" placeholder="Search (e.g. levis, nike, 90s ...)">
                    <button onclick="applyFilters()">Search</button>
                </div>
            </div>
            <div class="filters-row">
                <div class="filter-group">
                    <label>Category</label>
                    <select id="queryFilter" onchange="applyFilters()"><option value="">All</option></select>
                </div>
                <div class="filter-group">
                    <label>Sort</label>
                    <select id="sort" onchange="applyFilters()">
                        <option value="newest">Newest</option>
                        <option value="price_low">Price Low</option>
                        <option value="price_high">Price High</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Min Price ($)</label>
                    <input type="number" id="minPrice" placeholder="0" min="0">
                </div>
                <div class="filter-group">
                    <label>Max Price ($)</label>
                    <input type="number" id="maxPrice" placeholder="1000" min="0">
                </div>
            </div>
        </section>
        <section class="results-info" id="resultsInfo" style="display:none;">
            <div class="results-info-inner">
                <span id="totalCount"></span>
                <div class="view-toggle">
                    <button class="view-btn active" data-view="grid" onclick="setView('grid')">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="1" width="6" height="6" rx="1"/><rect x="9" y="1" width="6" height="6" rx="1"/><rect x="1" y="9" width="6" height="6" rx="1"/><rect x="9" y="9" width="6" height="6" rx="1"/></svg>
                    </button>
                    <button class="view-btn" data-view="list" onclick="setView('list')">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="1" width="14" height="3" rx="1"/><rect x="1" y="6" width="14" height="3" rx="1"/><rect x="1" y="11" width="14" height="3" rx="1"/></svg>
                    </button>
                </div>
            </div>
        </section>
        <section class="results-container"><div class="results grid-view" id="results"></div></section>
        <div class="pagination" id="pagination" style="display:none;">
            <button id="prevBtn" onclick="changePage(-1)">Prev</button>
            <span id="pageInfo"></span>
            <button id="nextBtn" onclick="changePage(1)">Next</button>
        </div>
        <section class="favorites-section" id="favoritesSection" style="display:none;">
            <div class="fav-header">
                <h2>Saved (<span id="favCount">0</span>)</h2>
                <div class="fav-actions">
                    <button onclick="exportFavorites()">CSV Download</button>
                    <button onclick="clearFavorites()" class="btn-danger">Clear All</button>
                </div>
            </div>
            <div class="fav-list" id="favList"></div>
        </section>
    </main>
    <button class="fab" id="fabBtn" onclick="toggleFavorites()" style="display:none;">&#9829; <span id="fabCount">0</span></button>
    <script>
    const RAW_DATA = {data_json};
    let currentPlatform = 'all';
    let currentPage = 1;
    let filteredItems = [];
    const PER_PAGE = 48;
    let favorites = JSON.parse(localStorage.getItem('vf_favorites') || '[]');

    document.getElementById('searchText').addEventListener('keypress', e => {{ if (e.key === 'Enter') applyFilters(); }});

    // Init
    RAW_DATA.queries.forEach(q => {{
        const opt = document.createElement('option');
        opt.value = q; opt.textContent = q;
        document.getElementById('queryFilter').appendChild(opt);
    }});
    if (RAW_DATA.crawled_at) {{
        const parts = [];
        if (RAW_DATA.crawled_at.ebay) parts.push('eBay: ' + fmtDate(RAW_DATA.crawled_at.ebay));
        if (RAW_DATA.crawled_at.depop) parts.push('Depop: ' + fmtDate(RAW_DATA.crawled_at.depop));
        document.getElementById('crawlInfo').textContent = 'Last Updated: ' + parts.join(' | ');
    }}
    updateFavUI();
    applyFilters();

    function fmtDate(iso) {{
        if (!iso) return '';
        const d = new Date(iso);
        return d.toLocaleDateString('en-US', {{ month: 'short', day: 'numeric' }}) + ' ' + d.toLocaleTimeString('en-US', {{ hour: '2-digit', minute: '2-digit' }});
    }}

    function setPlatform(p) {{
        currentPlatform = p;
        document.querySelectorAll('.platform-tab').forEach(t => t.classList.toggle('active', t.dataset.platform === p));
        applyFilters();
    }}

    function extractPrice(s) {{
        const m = s.replace(/,/g, '').match(/[\\d]+\\.?\\d*/);
        return m ? parseFloat(m[0]) : null;
    }}

    function applyFilters() {{
        let items = RAW_DATA.items;
        if (currentPlatform !== 'all') items = items.filter(i => i._platform === currentPlatform);
        const q = document.getElementById('queryFilter').value;
        if (q) items = items.filter(i => i.query === q);
        const search = document.getElementById('searchText').value.toLowerCase();
        if (search) items = items.filter(i => i.title.toLowerCase().includes(search));
        const minP = document.getElementById('minPrice').value;
        const maxP = document.getElementById('maxPrice').value;
        if (minP) items = items.filter(i => (extractPrice(i.price) || 0) >= parseFloat(minP));
        if (maxP) items = items.filter(i => {{ const p = extractPrice(i.price); return p !== null && p <= parseFloat(maxP); }});
        const sort = document.getElementById('sort').value;
        if (sort === 'price_low') items.sort((a, b) => (extractPrice(a.price) || 999999) - (extractPrice(b.price) || 999999));
        else if (sort === 'price_high') items.sort((a, b) => (extractPrice(b.price) || 0) - (extractPrice(a.price) || 0));
        filteredItems = items;
        currentPage = 1;
        renderPage();
    }}

    function renderPage() {{
        const total = filteredItems.length;
        const totalPages = Math.max(1, Math.ceil(total / PER_PAGE));
        const start = (currentPage - 1) * PER_PAGE;
        const pageItems = filteredItems.slice(start, start + PER_PAGE);

        document.getElementById('totalCount').textContent = total + ' items';
        document.getElementById('resultsInfo').style.display = total > 0 ? 'flex' : 'none';
        document.getElementById('pagination').style.display = total > PER_PAGE ? 'flex' : 'none';
        document.getElementById('pageInfo').textContent = currentPage + ' / ' + totalPages;
        document.getElementById('prevBtn').disabled = currentPage <= 1;
        document.getElementById('nextBtn').disabled = currentPage >= totalPages;

        const container = document.getElementById('results');
        if (!pageItems.length) {{
            container.innerHTML = '<div class="no-results">No results found.</div>';
            return;
        }}
        container.innerHTML = pageItems.map((item, i) => {{
            const idx = start + i;
            const isFav = favorites.some(f => f.link === item.link);
            const p = item._platform || 'ebay';
            const badge = p === 'depop' ? 'depop-badge' : 'ebay-badge';
            const linkCls = p === 'depop' ? 'item-link depop-link' : 'item-link';
            const btnText = p === 'depop' ? 'View on Depop' : 'View on eBay';
            return `<div class="item-card">
                <div class="item-image">
                    <img src="${{item.image || ''}}" alt="${{item.title}}" loading="lazy" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 200 200%22><rect fill=%22%23f0f0f0%22 width=%22200%22 height=%22200%22/><text x=%2250%%22 y=%2250%%22 text-anchor=%22middle%22 fill=%22%23999%22 font-size=%2214%22>No Image</text></svg>'">
                    <button class="fav-btn ${{isFav ? 'active' : ''}}" onclick="toggleFav(${{idx}})" data-index="${{idx}}">${{isFav ? '&#9829;' : '&#9825;'}}</button>
                    <span class="platform-badge ${{badge}}">${{p === 'depop' ? 'Depop' : 'eBay'}}</span>
                </div>
                <div class="item-info">
                    <h3 class="item-title" title="${{item.title}}">${{item.title}}</h3>
                    <div class="item-price">${{item.price}}</div>
                    <div class="item-meta">
                        ${{item.condition ? `<span class="meta-tag">${{item.condition}}</span>` : ''}}
                        ${{item.shipping ? `<span class="meta-tag shipping">${{item.shipping}}</span>` : ''}}
                        ${{item.query ? `<span class="meta-tag query">${{item.query}}</span>` : ''}}
                    </div>
                    ${{item.seller ? `<div class="item-seller">${{item.seller}}</div>` : ''}}
                    ${{item.extra ? `<div class="item-location">${{item.extra}}</div>` : ''}}
                    <a href="${{item.link}}" target="_blank" class="${{linkCls}}">${{btnText}} &rarr;</a>
                </div>
            </div>`;
        }}).join('');
        window._currentItems = filteredItems;
    }}

    function setView(v) {{
        document.getElementById('results').className = 'results ' + v + '-view';
        document.querySelectorAll('.view-btn').forEach(b => b.classList.toggle('active', b.dataset.view === v));
    }}

    function changePage(d) {{
        const totalPages = Math.max(1, Math.ceil(filteredItems.length / PER_PAGE));
        const next = currentPage + d;
        if (next >= 1 && next <= totalPages) {{ currentPage = next; renderPage(); window.scrollTo({{top:0,behavior:'smooth'}}); }}
    }}

    function toggleFav(idx) {{
        const item = filteredItems[idx];
        const ei = favorites.findIndex(f => f.link === item.link);
        if (ei >= 0) favorites.splice(ei, 1);
        else favorites.push({{ ...item, addedAt: new Date().toISOString() }});
        localStorage.setItem('vf_favorites', JSON.stringify(favorites));
        updateFavUI(); renderPage();
    }}

    function updateFavUI() {{
        const c = favorites.length;
        document.getElementById('favCount').textContent = c;
        document.getElementById('fabCount').textContent = c;
        document.getElementById('fabBtn').style.display = c > 0 ? 'flex' : 'none';
        const fl = document.getElementById('favList');
        if (!c) {{ fl.innerHTML = '<p class="fav-empty">No saved items.</p>'; return; }}
        fl.innerHTML = favorites.map((item, i) => `<div class="fav-item">
            <img src="${{item.image||''}}" class="fav-thumb" onerror="this.style.display='none'">
            <div class="fav-info">
                <div class="fav-title">${{item.title}}</div>
                <div class="fav-price">${{item.price}} <span class="fav-platform-tag">${{(item._platform||item.platform||'ebay').toUpperCase()}}</span></div>
            </div>
            <div class="fav-actions-item">
                <a href="${{item.link}}" target="_blank" class="btn-sm">View</a>
                <button class="btn-sm btn-danger" onclick="removeFav(${{i}})">Remove</button>
            </div>
        </div>`).join('');
    }}

    function removeFav(i) {{ favorites.splice(i,1); localStorage.setItem('vf_favorites',JSON.stringify(favorites)); updateFavUI(); }}
    function clearFavorites() {{ if(confirm('Clear all saved items?')){{ favorites=[]; localStorage.setItem('vf_favorites','[]'); updateFavUI(); document.getElementById('favoritesSection').style.display='none'; }} }}
    function toggleFavorites() {{ const s=document.getElementById('favoritesSection'); const v=s.style.display!=='none'; s.style.display=v?'none':'block'; if(!v)s.scrollIntoView({{behavior:'smooth'}}); }}
    function exportFavorites() {{
        if(!favorites.length)return;
        const h=['Platform','Title','Price','Condition','Shipping','Seller','Link'];
        const rows=favorites.map(f=>[`"${{(f._platform||f.platform||'ebay').toUpperCase()}}"`,`"${{f.title.replace(/"/g,'""')}}"`,`"${{f.price}}"`,`"${{f.condition||''}}"`,`"${{f.shipping||''}}"`,`"${{f.seller||''}}"`,f.link]);
        const csv='\\uFEFF'+[h.join(','),...rows.map(r=>r.join(','))].join('\\n');
        const blob=new Blob([csv],{{type:'text/csv;charset=utf-8;'}});
        const u=URL.createObjectURL(blob); const a=document.createElement('a');
        a.href=u; a.download=`vintage-finder-${{new Date().toISOString().slice(0,10)}}.csv`; a.click(); URL.revokeObjectURL(u);
    }}
    </script>
</body>
</html>'''


CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif; background:#f5f5f7; color:#1d1d1f; min-height:100vh; }
header { background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%); color:white; padding:2rem 0; text-align:center; }
.header-inner h1 { font-size:2rem; font-weight:700; letter-spacing:-0.5px; }
.subtitle { margin-top:0.3rem; font-size:0.95rem; color:rgba(255,255,255,0.7); font-weight:300; }
.crawl-info { margin-top:0.5rem; font-size:0.75rem; color:rgba(255,255,255,0.45); }
main { max-width:1280px; margin:0 auto; padding:1.5rem; }
.platform-tabs { display:flex; gap:0.5rem; margin-bottom:1rem; }
.platform-tab { flex:1; display:flex; align-items:center; justify-content:center; gap:0.5rem; padding:0.85rem 1rem; background:white; border:2px solid #e5e5ea; border-radius:12px; cursor:pointer; font-family:inherit; transition:all 0.2s; }
.platform-tab:hover { border-color:#0f3460; }
.platform-tab.active { border-color:#0f3460; background:#f0f4ff; }
.tab-label { font-size:0.95rem; font-weight:600; }
.search-panel { background:white; border-radius:16px; padding:1.5rem; box-shadow:0 2px 12px rgba(0,0,0,0.06); margin-bottom:1.5rem; }
.search-row { margin-bottom:1rem; }
.search-input-wrap { display:flex; gap:0.75rem; }
.search-input-wrap input { flex:1; padding:0.85rem 1.2rem; border:2px solid #e5e5ea; border-radius:12px; font-size:1rem; font-family:inherit; transition:border-color 0.2s; }
.search-input-wrap input:focus { outline:none; border-color:#0f3460; }
.search-input-wrap button { padding:0.85rem 2rem; background:#0f3460; color:white; border:none; border-radius:12px; font-size:1rem; font-weight:600; cursor:pointer; transition:background 0.2s; font-family:inherit; }
.search-input-wrap button:hover { background:#1a1a2e; }
.filters-row { display:flex; gap:1rem; flex-wrap:wrap; }
.filter-group { display:flex; flex-direction:column; gap:0.3rem; flex:1; min-width:140px; }
.filter-group label { font-size:0.78rem; font-weight:600; color:#86868b; text-transform:uppercase; letter-spacing:0.5px; }
.filter-group select, .filter-group input { padding:0.6rem 0.8rem; border:2px solid #e5e5ea; border-radius:10px; font-size:0.9rem; font-family:inherit; background:white; transition:border-color 0.2s; }
.filter-group select:focus, .filter-group input:focus { outline:none; border-color:#0f3460; }
.results-info { display:flex; margin-bottom:1rem; }
.results-info-inner { display:flex; align-items:center; gap:1rem; width:100%; padding:0.75rem 0; }
#totalCount { font-size:0.9rem; color:#86868b; font-weight:500; }
.view-toggle { display:flex; gap:0.25rem; margin-left:auto; }
.view-btn { padding:0.4rem 0.6rem; border:1px solid #e5e5ea; background:white; border-radius:8px; cursor:pointer; color:#86868b; transition:all 0.2s; }
.view-btn.active { background:#0f3460; color:white; border-color:#0f3460; }
.results.grid-view { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:1.25rem; }
.results.list-view { display:flex; flex-direction:column; gap:0.75rem; }
.results.list-view .item-card { flex-direction:row; }
.results.list-view .item-image { width:180px; min-height:140px; flex-shrink:0; padding-top:0; }
.item-card { background:white; border-radius:14px; overflow:hidden; box-shadow:0 1px 8px rgba(0,0,0,0.06); display:flex; flex-direction:column; transition:transform 0.2s,box-shadow 0.2s; }
.item-card:hover { transform:translateY(-2px); box-shadow:0 4px 20px rgba(0,0,0,0.1); }
.item-image { position:relative; padding-top:100%; background:#f5f5f7; overflow:hidden; }
.item-image img { position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover; }
.fav-btn { position:absolute; top:0.5rem; right:0.5rem; width:36px; height:36px; border-radius:50%; border:none; background:rgba(255,255,255,0.9); font-size:1.2rem; cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s; backdrop-filter:blur(4px); z-index:2; }
.fav-btn:hover { transform:scale(1.1); }
.fav-btn.active { background:#ff3b5c; color:white; }
.platform-badge { position:absolute; top:0.5rem; left:0.5rem; padding:0.15rem 0.5rem; border-radius:6px; font-size:0.7rem; font-weight:700; z-index:2; backdrop-filter:blur(4px); }
.ebay-badge { background:rgba(227,34,27,0.9); color:white; }
.depop-badge { background:rgba(255,35,0,0.9); color:white; }
.item-info { padding:1rem; display:flex; flex-direction:column; gap:0.4rem; }
.item-title { font-size:0.9rem; font-weight:500; line-height:1.3; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.item-price { font-size:1.15rem; font-weight:700; color:#0f3460; }
.item-meta { display:flex; gap:0.4rem; flex-wrap:wrap; }
.meta-tag { font-size:0.75rem; padding:0.2rem 0.5rem; background:#f5f5f7; border-radius:6px; color:#555; }
.meta-tag.shipping { color:#1a8917; background:#e8f5e9; }
.meta-tag.query { color:#0f3460; background:#e8eaf6; }
.item-seller { font-size:0.8rem; color:#86868b; }
.item-location { font-size:0.78rem; color:#aaabb0; }
.item-link { display:inline-block; margin-top:0.5rem; padding:0.55rem 1rem; background:#0f3460; color:white; text-decoration:none; border-radius:10px; font-size:0.82rem; font-weight:600; text-align:center; transition:background 0.2s; }
.item-link:hover { background:#1a1a2e; }
.item-link.depop-link { background:#ff2300; }
.item-link.depop-link:hover { background:#cc1c00; }
.pagination { display:flex; align-items:center; justify-content:center; gap:1.5rem; padding:2rem 0; }
.pagination button { padding:0.6rem 1.5rem; border:2px solid #e5e5ea; background:white; border-radius:10px; font-size:0.9rem; cursor:pointer; font-family:inherit; font-weight:500; transition:all 0.2s; }
.pagination button:hover:not(:disabled) { border-color:#0f3460; color:#0f3460; }
.pagination button:disabled { opacity:0.4; cursor:not-allowed; }
#pageInfo { font-size:0.9rem; color:#86868b; font-weight:500; }
.no-results { text-align:center; padding:4rem 2rem; color:#86868b; font-size:1rem; }
.fab { position:fixed; bottom:2rem; right:2rem; width:56px; height:56px; border-radius:50%; background:#ff3b5c; color:white; border:none; font-size:1.1rem; cursor:pointer; box-shadow:0 4px 16px rgba(255,59,92,0.4); display:flex; align-items:center; justify-content:center; gap:0.2rem; transition:transform 0.2s; z-index:100; }
.fab:hover { transform:scale(1.1); }
#fabCount { font-size:0.8rem; font-weight:700; }
.favorites-section { margin-top:2rem; background:white; border-radius:16px; padding:1.5rem; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
.fav-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem; flex-wrap:wrap; gap:0.75rem; }
.fav-header h2 { font-size:1.2rem; font-weight:600; }
.fav-actions { display:flex; gap:0.5rem; }
.fav-actions button { padding:0.5rem 1rem; border:1px solid #e5e5ea; background:white; border-radius:8px; font-size:0.82rem; cursor:pointer; font-family:inherit; font-weight:500; transition:all 0.2s; }
.fav-actions button:hover { border-color:#0f3460; }
.btn-danger { color:#ff3b5c!important; border-color:#ffd6dd!important; }
.btn-danger:hover { background:#fff0f3!important; }
.fav-item { display:flex; align-items:center; gap:1rem; padding:0.75rem; border-bottom:1px solid #f5f5f7; }
.fav-item:last-child { border-bottom:none; }
.fav-thumb { width:60px; height:60px; border-radius:8px; object-fit:cover; background:#f5f5f7; }
.fav-info { flex:1; min-width:0; }
.fav-title { font-size:0.85rem; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.fav-price { font-size:0.9rem; font-weight:700; color:#0f3460; }
.fav-platform-tag { font-size:0.65rem; padding:0.1rem 0.4rem; background:#e8eaf6; border-radius:4px; color:#0f3460; font-weight:600; margin-left:0.3rem; }
.fav-actions-item { display:flex; gap:0.4rem; flex-shrink:0; }
.btn-sm { padding:0.35rem 0.75rem; border:1px solid #e5e5ea; background:white; border-radius:6px; font-size:0.78rem; cursor:pointer; text-decoration:none; color:#1d1d1f; font-family:inherit; transition:all 0.2s; }
.btn-sm:hover { border-color:#0f3460; }
.fav-empty { text-align:center; padding:2rem; color:#86868b; }
@media (max-width:768px) { main{padding:1rem;} .search-input-wrap{flex-direction:column;} .filters-row{flex-direction:column;} .results.grid-view{grid-template-columns:1fr 1fr;} .results.list-view .item-card{flex-direction:column;} .results.list-view .item-image{width:100%;padding-top:60%;} .results-info-inner{flex-wrap:wrap;} .fav-item{flex-wrap:wrap;} }
@media (max-width:480px) { .results.grid-view{grid-template-columns:1fr;} header{padding:1.5rem 0;} .header-inner h1{font-size:1.5rem;} .platform-tabs{gap:0.3rem;} .platform-tab{padding:0.6rem;} }
"""


if __name__ == "__main__":
    build()

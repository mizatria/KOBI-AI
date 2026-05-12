/* =====================
   KOBİ STORE — store.js
   API Base: FastAPI backend
   ===================== */

const API_BASE = '';  // Aynı origin, gerekirse 'http://localhost:8000' yaz

let allProducts = [];
let activeCategory = 'all';
let selectedProduct = null;

/* =====================
   INIT
   ===================== */
document.addEventListener('DOMContentLoaded', async () => {
  renderSkeletons();
  await loadCategories();
  await loadProducts();
  bindModalEvents();
  bindSearch();
  bindQuantityChange();
});

/* =====================
   SKELETONS
   ===================== */
function renderSkeletons(count = 8) {
  const grid = document.getElementById('products-grid');
  grid.innerHTML = Array.from({ length: count }, () => `
    <div class="skeleton-card">
      <div class="skeleton-inner">
        <div class="skel-line title"></div>
        <div class="skel-line desc"></div>
        <div class="skel-line desc2"></div>
        <div class="skel-line price"></div>
      </div>
    </div>
  `).join('');
}

/* =====================
   LOAD CATEGORIES
   ===================== */
async function loadCategories() {
  try {
    const res = await fetch(`${API_BASE}/products/store/categories`);
    if (!res.ok) return;
    const cats = await res.json();

    const list = document.getElementById('category-list');
    cats.forEach(cat => {
      if (!cat) return;
      const btn = document.createElement('button');
      btn.className = 'cat-btn';
      btn.dataset.cat = cat;
      btn.textContent = cat;
      btn.addEventListener('click', () => filterByCategory(cat, btn));
      list.appendChild(btn);
    });
  } catch (e) {
    console.warn('Kategoriler yüklenemedi:', e);
  }
}

/* =====================
   LOAD PRODUCTS
   ===================== */
async function loadProducts(category = null) {
  try {
    let url = `${API_BASE}/products/store`;
    if (category && category !== 'all') url += `?category=${encodeURIComponent(category)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Ürünler alınamadı');
    allProducts = await res.json();
    renderProducts(allProducts);
  } catch (e) {
    console.error(e);
    document.getElementById('products-grid').innerHTML = `
      <p style="color:var(--red); grid-column:1/-1; text-align:center; padding:40px;">
        Ürünler yüklenirken bir hata oluştu.
      </p>`;
  }
}

/* =====================
   RENDER PRODUCTS
   ===================== */
function renderProducts(products) {
  const grid = document.getElementById('products-grid');
  const empty = document.getElementById('empty-state');

  if (!products.length) {
    grid.innerHTML = '';
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';

  grid.innerHTML = products.map((p, i) => {
    const stockStatus = getStockStatus(p);
    return `
      <div class="product-card" style="animation-delay:${i * 0.06}s" data-id="${p.id}">
        <div class="card-badge">
          <span class="card-category">${p.category || '—'}</span>
          <span class="card-stock ${stockStatus.cls}">${stockStatus.label}</span>
        </div>
        <div class="card-body">
          <div class="card-name">${escHtml(p.name)}</div>
          <div class="card-desc">${escHtml(p.description || '')}</div>
          <div class="card-footer">
            <div>
              <span class="card-price">₺${Number(p.price).toFixed(2)}</span>
              <span class="card-unit">/ ${escHtml(p.unit || '')}</span>
            </div>
            <button class="card-order-btn" onclick="openOrderModal(${p.id}, event)">
              Sipariş Ver
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function getStockStatus(p) {
  if (!p.stock || p.stock <= 0)          return { cls: 'out', label: 'Stok Yok' };
  if (p.stock <= (p.min_stock_limit || 0)) return { cls: 'low', label: 'Az Kaldı' };
  return { cls: 'ok', label: 'Stokta' };
}

/* =====================
   FILTER BY CATEGORY
   ===================== */
function filterByCategory(cat, clickedBtn) {
  activeCategory = cat;
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
  clickedBtn.classList.add('active');

  const searchVal = document.getElementById('search-input').value.toLowerCase();
  applyFilters(cat, searchVal);
}

/* =====================
   SEARCH
   ===================== */
function bindSearch() {
  document.getElementById('search-input').addEventListener('input', (e) => {
    const val = e.target.value.toLowerCase();
    applyFilters(activeCategory, val);
  });
}

// All-button
document.addEventListener('DOMContentLoaded', () => {
  const allBtn = document.querySelector('.cat-btn[data-cat="all"]');
  if (allBtn) {
    allBtn.addEventListener('click', () => filterByCategory('all', allBtn));
  }
});

/* =====================
   APPLY FILTERS
   ===================== */
function applyFilters(category, search) {
  let filtered = allProducts;

  if (category && category !== 'all') {
    filtered = filtered.filter(p => p.category === category);
  }

  if (search) {
    filtered = filtered.filter(p =>
      (p.name || '').toLowerCase().includes(search) ||
      (p.description || '').toLowerCase().includes(search) ||
      (p.category || '').toLowerCase().includes(search)
    );
  }

  renderProducts(filtered);
}

/* =====================
   OPEN ORDER MODAL
   ===================== */
function openOrderModal(productId, event) {
  event && event.stopPropagation();
  selectedProduct = allProducts.find(p => p.id === productId);
  if (!selectedProduct) return;

  // Ürün bilgisini doldur
  document.getElementById('modal-product-info').innerHTML = `
    <div class="mp-category">${escHtml(selectedProduct.category || '')}</div>
    <div class="mp-name">${escHtml(selectedProduct.name)}</div>
    <div class="mp-price">₺${Number(selectedProduct.price).toFixed(2)} / ${escHtml(selectedProduct.unit || '')}</div>
  `;

  // Unit badge
  document.getElementById('unit-label').textContent = selectedProduct.unit || '';

  // Formu sıfırla
  document.getElementById('order-form').reset();
  document.getElementById('quantity').value = '1';
  document.getElementById('form-feedback').textContent = '';
  document.getElementById('form-feedback').className = 'form-feedback';
  document.getElementById('stock-alert').style.display = 'none';
  document.getElementById('submit-btn').disabled = false;
  document.getElementById('btn-text').style.display = 'inline';
  document.getElementById('btn-loader').style.display = 'none';

  updateTotalPrice();

  // Modal aç
  document.getElementById('modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

/* =====================
   CLOSE MODAL
   ===================== */
function bindModalEvents() {
  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target === document.getElementById('modal-overlay')) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });

  document.getElementById('submit-btn').addEventListener('click', submitOrder);
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  document.body.style.overflow = '';
  selectedProduct = null;
}

/* =====================
   PRICE PREVIEW
   ===================== */
function bindQuantityChange() {
  document.getElementById('quantity').addEventListener('input', updateTotalPrice);
}

function updateTotalPrice() {
  if (!selectedProduct) return;
  const qty = parseFloat(document.getElementById('quantity').value) || 0;
  const total = (selectedProduct.price * qty).toFixed(2);
  document.getElementById('total-price').textContent = `₺${total}`;
}

/* =====================
   SUBMIT ORDER
   ===================== */
async function submitOrder() {
  if (!selectedProduct) return;

  const first_name    = document.getElementById('first_name').value.trim();
  const last_name     = document.getElementById('last_name').value.trim();
  const phone_number  = document.getElementById('phone_number').value.trim();
  const quantity      = parseFloat(document.getElementById('quantity').value);

  if (!first_name || !last_name || !phone_number || !quantity || quantity <= 0) {
    showFeedback('Lütfen tüm alanları doldurun.', 'error');
    return;
  }

  const payload = {
    first_name,
    last_name,
    phone_number,
    product_id: selectedProduct.id,
    quantity,
  };

  // Loading
  document.getElementById('submit-btn').disabled = true;
  document.getElementById('btn-text').style.display = 'none';
  document.getElementById('btn-loader').style.display = 'inline';
  showFeedback('', '');

  try {
    const res = await fetch(`${API_BASE}/orders/store`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
      showFeedback(data.detail || 'Sipariş oluşturulamadı.', 'error');
      return;
    }

    showFeedback('✅ Siparişiniz alındı! Teşekkürler.', 'success');

    // Stok uyarısı varsa göster
    if (data.stock_alert) {
      const alert = document.getElementById('stock-alert');
      document.getElementById('stock-warning-text').textContent = data.stock_alert.warning;
      const waLink = document.getElementById('wa-link');
      if (data.stock_alert.wa_link) {
        waLink.href = data.stock_alert.wa_link;
        waLink.style.display = 'inline-flex';
      } else {
        waLink.style.display = 'none';
      }
      alert.style.display = 'block';
    }

    // Ürünleri güncelle (stok düşmüş olabilir)
    setTimeout(() => {
      loadProducts(activeCategory !== 'all' ? activeCategory : null);
    }, 1500);

  } catch (e) {
    showFeedback('Bağlantı hatası. Lütfen tekrar deneyin.', 'error');
  } finally {
    document.getElementById('submit-btn').disabled = false;
    document.getElementById('btn-text').style.display = 'inline';
    document.getElementById('btn-loader').style.display = 'none';
  }
}

/* =====================
   HELPERS
   ===================== */
function showFeedback(msg, type) {
  const el = document.getElementById('form-feedback');
  el.textContent = msg;
  el.className = `form-feedback ${type}`;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
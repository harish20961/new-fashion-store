const API_BASE_URL = "http://localhost:5000/api";

// ---------- Small helpers (used on every page) ----------

// Escapes text before it goes into innerHTML, so product names or reviews
// can never inject HTML/JS into the page.
function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatPrice(amount) {
  return "₹" + Number(amount).toLocaleString("en-IN");
}

// ---------- Session helpers ----------
function saveSession(token, name, role) {
  localStorage.setItem("fh_token", token);
  localStorage.setItem("fh_name", name);
  localStorage.setItem("fh_role", role);
}

function getToken() {
  return localStorage.getItem("fh_token");
}

function logout() {
  localStorage.removeItem("fh_token");
  localStorage.removeItem("fh_name");
  localStorage.removeItem("fh_role");
  window.location.href = "index.html";
}

function updateHeaderForAuth() {
  const loginLink = document.getElementById("loginLink");
  if (!loginLink) return;

  const name = localStorage.getItem("fh_name");
  if (name) {
    loginLink.textContent = `Hi, ${name}`;
    loginLink.href = "#";
    loginLink.onclick = (e) => {
      e.preventDefault();
      logout();
    };
  } else {
    loginLink.textContent = "Log in";
    loginLink.removeAttribute("onclick");
    loginLink.href = "login.html";
  }
}

// Shows "Cart (3)" in the header. Other scripts call this after changing the cart.
async function updateCartCount() {
  const cartLink = document.getElementById("cartLink");
  const token = getToken();
  if (!cartLink) return;
  if (!token) {
    cartLink.textContent = "Cart";
    return;
  }
  try {
    const res = await fetch(`${API_BASE_URL}/cart`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const items = await res.json();
    const count = items.reduce((sum, item) => sum + item.quantity, 0);
    cartLink.textContent = count > 0 ? `Cart (${count})` : "Cart";
  } catch (err) {
    /* header count is a nicety; ignore network errors */
  }
}

// =====================================================================
// Homepage: search, filters, sorting
// All filter choices live in the URL (e.g. index.html?category=Men&sort=price_asc)
// so a filtered view can be bookmarked, shared, and works with the back button.
// =====================================================================

const SORT_DEFAULT = "newest";
let latestRequest = 0; // lets us ignore slow responses that arrive out of order

function splitList(value) {
  return value ? value.split(",").filter(Boolean) : [];
}

function readStateFromUrl() {
  const p = new URLSearchParams(window.location.search);
  return {
    category: p.get("category") || "",
    search: p.get("search") || "",
    sort: p.get("sort") || SORT_DEFAULT,
    min_price: p.get("min_price") || "",
    max_price: p.get("max_price") || "",
    size: splitList(p.get("size")),
    color: splitList(p.get("color")),
    brand: splitList(p.get("brand")),
    in_stock: p.get("in_stock") === "1",
  };
}

// Turns the state object into query-string params (leaving out empty/default values)
function stateToParams(state) {
  const params = new URLSearchParams();
  if (state.category) params.set("category", state.category);
  if (state.search) params.set("search", state.search);
  if (state.sort && state.sort !== SORT_DEFAULT) params.set("sort", state.sort);
  if (state.min_price !== "") params.set("min_price", state.min_price);
  if (state.max_price !== "") params.set("max_price", state.max_price);
  if (state.size.length) params.set("size", state.size.join(","));
  if (state.color.length) params.set("color", state.color.join(","));
  if (state.brand.length) params.set("brand", state.brand.join(","));
  if (state.in_stock) params.set("in_stock", "1");
  return params;
}

function countActiveFilters(state) {
  return (
    (state.category ? 1 : 0) +
    (state.min_price !== "" || state.max_price !== "" ? 1 : 0) +
    state.size.length + state.color.length + state.brand.length +
    (state.in_stock ? 1 : 0)
  );
}

function chipGroup(title, name, values, selected) {
  if (!values.length) return "";
  const chips = values
    .map(
      (v) => `
      <label class="chip-check">
        <input type="checkbox" name="${name}" value="${esc(v)}" ${selected.includes(v) ? "checked" : ""}>
        <span>${esc(v)}</span>
      </label>`
    )
    .join("");
  return `<fieldset class="filter-group"><legend>${title}</legend><div class="chip-row">${chips}</div></fieldset>`;
}

function buildFilterPanel(options, state) {
  const form = document.getElementById("filterForm");
  const categoryOptions = [`<option value="">All categories</option>`]
    .concat(
      options.categories.map(
        (c) => `<option value="${esc(c)}" ${state.category === c ? "selected" : ""}>${esc(c)}</option>`
      )
    )
    .join("");

  form.innerHTML = `
    <div class="filters-head">
      <h3>Filters</h3>
      <button type="button" id="resetFilters" class="link-button">Reset all</button>
    </div>

    <fieldset class="filter-group">
      <legend>Category</legend>
      <select name="category" class="filter-select">${categoryOptions}</select>
    </fieldset>

    <fieldset class="filter-group">
      <legend>Price (₹)</legend>
      <div class="price-inputs">
        <input type="number" name="min_price" min="0" placeholder="${options.min_price}" value="${esc(state.min_price)}" aria-label="Minimum price">
        <span>to</span>
        <input type="number" name="max_price" min="0" placeholder="${options.max_price}" value="${esc(state.max_price)}" aria-label="Maximum price">
      </div>
    </fieldset>

    ${chipGroup("Size", "size", options.sizes, state.size)}
    ${chipGroup("Colour", "color", options.colors, state.color)}
    ${chipGroup("Brand", "brand", options.brands, state.brand)}

    <label class="stock-toggle">
      <input type="checkbox" name="in_stock" ${state.in_stock ? "checked" : ""}>
      <span>In stock only</span>
    </label>
  `;
}

// Reads whatever is currently selected in the toolbar + filter panel
function readStateFromForm() {
  const form = document.getElementById("filterForm");
  const checked = (name) =>
    Array.from(form.querySelectorAll(`input[name="${name}"]:checked`)).map((el) => el.value);

  return {
    category: form.elements["category"] ? form.elements["category"].value : "",
    search: document.getElementById("searchInput").value.trim(),
    sort: document.getElementById("sortSelect").value,
    min_price: form.elements["min_price"] ? form.elements["min_price"].value.trim() : "",
    max_price: form.elements["max_price"] ? form.elements["max_price"].value.trim() : "",
    size: checked("size"),
    color: checked("color"),
    brand: checked("brand"),
    in_stock: !!(form.elements["in_stock"] && form.elements["in_stock"].checked),
  };
}

function headingFor(state) {
  if (state.search) return `Results for “${state.search}”`;
  if (state.category) return state.category;
  return countActiveFilters(state) ? "Products" : "New arrivals";
}

function productCardHtml(product) {
  const stock = Number(product.stock ?? 0);
  let badge = "";
  if (stock <= 0) badge = `<span class="stock-badge badge-out">Sold out</span>`;
  else if (stock <= 5) badge = `<span class="stock-badge badge-low">Only ${stock} left</span>`;

  const image = product.image_url
    ? `<img src="${esc(product.image_url)}" alt="${esc(product.name)}" loading="lazy" onerror="this.remove()">`
    : "";

  return `
    <a class="product-card ${stock <= 0 ? "is-sold-out" : ""}" href="product.html?id=${esc(product._id)}">
      <div class="product-image">${image}${badge}</div>
      ${product.brand ? `<div class="product-brand">${esc(product.brand)}</div>` : ""}
      <h3>${esc(product.name)}</h3>
      <div class="price">${formatPrice(product.price)}</div>
    </a>`;
}

async function fetchAndRenderProducts(state) {
  const grid = document.getElementById("productGrid");
  const status = document.getElementById("productStatus");
  const heading = document.getElementById("productsHeading");
  const clearFilter = document.getElementById("clearFilter");
  const toggle = document.getElementById("filterToggle");

  const active = countActiveFilters(state) + (state.search ? 1 : 0);
  heading.textContent = headingFor(state);
  clearFilter.hidden = active === 0 && state.sort === SORT_DEFAULT;
  toggle.textContent = countActiveFilters(state) ? `Filters (${countActiveFilters(state)})` : "Filters";

  const requestId = ++latestRequest;
  status.textContent = "Loading products...";

  try {
    const qs = stateToParams(state).toString();
    const response = await fetch(`${API_BASE_URL}/products${qs ? "?" + qs : ""}`);
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    const products = await response.json();
    if (requestId !== latestRequest) return; // a newer search has already replaced this one

    if (products.length === 0) {
      status.textContent = "No products match your search or filters.";
      grid.innerHTML = `<p class="empty-state">Nothing found. Try removing a filter or searching for something else.</p>`;
      return;
    }
    status.textContent = `${products.length} product${products.length === 1 ? "" : "s"}`;
    grid.innerHTML = products.map(productCardHtml).join("");
  } catch (error) {
    if (requestId !== latestRequest) return;
    status.textContent = "Couldn't reach the backend. Make sure Flask is running on port 5000.";
    grid.innerHTML = "";
    console.error("Failed to load products:", error);
  }
}

// Called whenever the user changes the search box, sort, or any filter
function applyFilters() {
  const state = readStateFromForm();
  const qs = stateToParams(state).toString();
  history.replaceState(null, "", `${window.location.pathname}${qs ? "?" + qs : ""}${window.location.hash}`);
  fetchAndRenderProducts(state);
}

function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

async function initShop() {
  const grid = document.getElementById("productGrid");
  if (!grid) return; // not on the homepage

  const state = readStateFromUrl();
  const searchInput = document.getElementById("searchInput");
  const sortSelect = document.getElementById("sortSelect");
  const form = document.getElementById("filterForm");
  const panel = document.getElementById("filtersPanel");

  searchInput.value = state.search;
  sortSelect.value = ["newest", "price_asc", "price_desc", "name_asc"].includes(state.sort) ? state.sort : SORT_DEFAULT;

  // Products first (so the page isn't blank while filter options load)
  fetchAndRenderProducts(state);

  // (Re)builds the filter panel for a category. Sizes/colours/brands that don't
  // exist in that category are dropped, along with any selections of them.
  async function loadFilterPanel(current) {
    try {
      const qs = current.category ? `?category=${encodeURIComponent(current.category)}` : "";
      const res = await fetch(`${API_BASE_URL}/products/filters${qs}`);
      if (!res.ok) throw new Error("filters failed");
      const options = await res.json();
      const keep = (picked, valid) => picked.filter((v) => valid.includes(v));
      current.size = keep(current.size, options.sizes);
      current.color = keep(current.color, options.colors);
      current.brand = keep(current.brand, options.brands);
      buildFilterPanel(options, current);
    } catch (err) {
      form.innerHTML = `<p class="status-text">Filters unavailable.</p>`;
    }
  }
  await loadFilterPanel(state);
  let panelCategory = state.category;

  // --- events ---
  document.getElementById("searchForm").addEventListener("submit", (e) => {
    e.preventDefault();
    applyFilters();
  });
  searchInput.addEventListener("input", debounce(applyFilters, 350));
  sortSelect.addEventListener("change", applyFilters);

  form.addEventListener("change", async (e) => {
    if (e.target.name === "category" && e.target.value !== panelCategory) {
      panelCategory = e.target.value;
      const next = readStateFromForm();
      await loadFilterPanel(next); // panel is redrawn with this category's options
    }
    applyFilters();
  });
  form.addEventListener("input", debounce((e) => {
    if (e.target.type === "number") applyFilters(); // price boxes
  }, 500));
  form.addEventListener("click", async (e) => {
    if (e.target.id !== "resetFilters") return;
    searchInput.value = "";
    panelCategory = "";
    await loadFilterPanel({
      category: "", search: "", sort: SORT_DEFAULT, min_price: "", max_price: "",
      size: [], color: [], brand: [], in_stock: false,
    });
    applyFilters();
  });
  document.getElementById("filterToggle").addEventListener("click", () => {
    panel.classList.toggle("open");
  });
}

document.addEventListener("DOMContentLoaded", () => {
  updateHeaderForAuth();
  updateCartCount();
  initShop();
});

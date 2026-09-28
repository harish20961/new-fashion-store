const API_BASE_URL = "http://localhost:5000/api";

// ---------- Session helpers (used on every page) ----------
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

// ---------- Homepage: load products (optionally filtered by category) ----------
async function loadProducts() {
  const grid = document.getElementById("productGrid");
  const status = document.getElementById("productStatus");
  const heading = document.getElementById("productsHeading");
  const clearFilter = document.getElementById("clearFilter");
  if (!grid || !status) return; // not on the homepage

  // e.g. index.html?category=Men  ->  category = "Men"
  const category = new URLSearchParams(window.location.search).get("category");

  let url = `${API_BASE_URL}/products`;
  if (category) {
    url += `?category=${encodeURIComponent(category)}`;
    if (heading) heading.textContent = category;
  }
  if (clearFilter) clearFilter.hidden = !category;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);

    const products = await response.json();

    if (products.length === 0) {
      status.textContent = category
        ? "No products in this category yet."
        : "No products yet.";
      grid.innerHTML = "";
      return;
    }

    status.textContent = `${products.length} product(s)`;
    grid.innerHTML = products
      .map(
        (product) => `
        <a class="product-card" href="product.html?id=${product._id}">
          <div class="product-image">${product.image_url ? `<img src="${product.image_url}" alt="${product.name}" loading="lazy" onerror="this.remove()">` : ""}</div>
          <h3>${product.name}</h3>
          <div class="price">₹${product.price}</div>
        </a>
      `
      )
      .join("");
  } catch (error) {
    status.textContent =
      "Couldn't reach the backend. Make sure Flask is running on port 5000.";
    console.error("Failed to load products:", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  updateHeaderForAuth();
  loadProducts();
});
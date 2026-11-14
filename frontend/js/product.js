const MAX_PER_ITEM = 10; // must match MAX_PER_ITEM in backend/routes/cart_routes.py

function optionGroup(label, id, values) {
  if (!values || values.length === 0) return "";
  const buttons = values
    .map((v) => `<button type="button" class="chip" data-value="${esc(v)}" aria-pressed="false">${esc(v)}</button>`)
    .join("");
  return `
    <div class="option-group">
      <div class="option-label">${label}: <strong id="${id}Chosen">select one</strong></div>
      <div class="chip-row" id="${id}Chips">${buttons}</div>
    </div>`;
}

function stockMessage(stock) {
  if (stock <= 0) return { text: "Out of stock", cls: "stock-out" };
  if (stock <= 5) return { text: `Only ${stock} left — order soon`, cls: "stock-low" };
  return { text: "In stock", cls: "stock-ok" };
}

async function loadProductDetail() {
  const wrap = document.getElementById("productDetailWrap");
  const productId = new URLSearchParams(window.location.search).get("id");

  if (!productId) {
    wrap.innerHTML = "<p>No product selected.</p>";
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/products/${productId}`);
    if (!res.ok) throw new Error("Product not found");
    const product = await res.json();

    const stock = Number(product.stock ?? 0);
    const maxQty = Math.max(1, Math.min(stock, MAX_PER_ITEM));
    const sizes = product.sizes || [];
    const colors = product.colors || [];
    const sm = stockMessage(stock);
    document.title = `${product.name} — FashionHub`;

    wrap.innerHTML = `
      <div class="product-detail-grid">
        <div class="product-detail-image">
          ${product.image_url ? `<img src="${esc(product.image_url)}" alt="${esc(product.name)}">` : ""}
        </div>
        <div class="product-detail-info">
          ${product.brand ? `<div class="product-brand">${esc(product.brand)}</div>` : ""}
          <h1>${esc(product.name)}</h1>
          <div class="product-detail-price">${formatPrice(product.price)}</div>
          <div class="product-detail-category">${esc(product.category)}${product.subcategory ? " · " + esc(product.subcategory) : ""}</div>
          ${product.description ? `<p class="product-description">${esc(product.description)}</p>` : ""}

          ${optionGroup("Size", "size", sizes)}
          ${optionGroup("Colour", "color", colors)}

          <p class="stock-line ${sm.cls}" id="stockInfo">${sm.text}</p>

          <div class="qty-row">
            <label for="qty">Quantity</label>
            <input type="number" id="qty" value="1" min="1" max="${maxQty}" ${stock <= 0 ? "disabled" : ""}>
          </div>

          <button id="addToCartBtn" class="btn-primary btn-full" ${stock <= 0 ? "disabled" : ""}>
            ${stock <= 0 ? "Sold out" : "Add to cart"}
          </button>
          <p id="cartMessage" class="auth-success" role="status"></p>
        </div>
      </div>
    `;

    // --- size / colour selection ---
    const selected = { size: null, color: null };
    [["size", "sizeChips", "sizeChosen"], ["color", "colorChips", "colorChosen"]].forEach(([key, chipsId, labelId]) => {
      const row = document.getElementById(chipsId);
      if (!row) return;
      row.addEventListener("click", (e) => {
        const btn = e.target.closest(".chip");
        if (!btn) return;
        selected[key] = btn.dataset.value;
        row.querySelectorAll(".chip").forEach((c) => {
          const on = c === btn;
          c.classList.toggle("selected", on);
          c.setAttribute("aria-pressed", on);
        });
        document.getElementById(labelId).textContent = btn.dataset.value;
        document.getElementById("cartMessage").textContent = "";
      });
    });

    // --- add to cart ---
    const messageBox = document.getElementById("cartMessage");
    const showMessage = (text, isError) => {
      messageBox.className = isError ? "auth-error" : "auth-success";
      messageBox.innerHTML = text;
    };

    document.getElementById("addToCartBtn").addEventListener("click", async () => {
      const token = getToken();
      if (!token) {
        showMessage("Please log in first.", true);
        setTimeout(() => (window.location.href = "login.html"), 1200);
        return;
      }
      if (sizes.length && !selected.size) return showMessage("Please select a size.", true);
      if (colors.length && !selected.color) return showMessage("Please select a colour.", true);

      const quantity = parseInt(document.getElementById("qty").value, 10);
      if (!Number.isInteger(quantity) || quantity < 1) return showMessage("Enter a valid quantity.", true);

      try {
        const res = await fetch(`${API_BASE_URL}/cart`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({ product_id: productId, quantity, size: selected.size, color: selected.color }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Could not add to cart");

        showMessage(`Added to cart! <a href="cart.html">View cart</a>`, false);
        updateCartCount();
      } catch (err) {
        showMessage(esc(err.message), true);
      }
    });
  } catch (err) {
    wrap.innerHTML = `<p>Couldn't load this product.</p>`;
    console.error(err);
  }
}

document.addEventListener("DOMContentLoaded", loadProductDetail);

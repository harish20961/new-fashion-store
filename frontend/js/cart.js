const CART_MAX_PER_ITEM = 10; // same limit as the backend

function showCartMessage(text, isError = true) {
  const box = document.getElementById("cartMessage");
  if (!box) return;
  box.className = isError ? "auth-error" : "auth-success";
  box.textContent = text;
}

function cartRowHtml(item) {
  const limit = Math.min(item.stock, CART_MAX_PER_ITEM);
  const subtotal = item.price * item.quantity;
  const variant = [item.size ? `Size ${esc(item.size)}` : "", item.color ? esc(item.color) : ""]
    .filter(Boolean)
    .join(" · ");

  let warning = "";
  if (item.unavailable) warning = "This product is no longer available.";
  else if (item.stock <= 0) warning = "Out of stock — please remove this item.";
  else if (item.quantity > item.stock) warning = `Only ${item.stock} left — please reduce the quantity.`;

  return `
    <div class="cart-row ${warning ? "has-warning" : ""}" data-id="${esc(item._id)}">
      <div class="cart-thumb">${item.image_url ? `<img src="${esc(item.image_url)}" alt="" onerror="this.remove()">` : ""}</div>
      <div class="cart-row-info">
        <h3>${esc(item.product_name)}</h3>
        ${variant ? `<div class="cart-variant">${variant}</div>` : ""}
        <div class="cart-row-price">${formatPrice(item.price)} each</div>
        ${warning ? `<div class="cart-warning">${esc(warning)}</div>` : ""}
      </div>
      <div class="qty-stepper" aria-label="Quantity">
        <button type="button" class="qty-btn" data-action="dec" ${item.quantity <= 1 ? "disabled" : ""} aria-label="Decrease quantity">−</button>
        <input type="number" class="qty-input" value="${item.quantity}" min="1" max="${Math.max(limit, 1)}" aria-label="Quantity">
        <button type="button" class="qty-btn" data-action="inc" ${item.quantity >= limit ? "disabled" : ""} aria-label="Increase quantity">+</button>
      </div>
      <div class="cart-line-total">${formatPrice(subtotal)}</div>
      <button class="btn-remove" data-action="remove">Remove</button>
    </div>`;
}

async function loadCart() {
  const token = getToken();
  const wrap = document.getElementById("cartWrap");

  if (!token) {
    wrap.innerHTML = `<p>Please <a href="login.html">log in</a> to view your cart.</p>`;
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/cart`, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw new Error("Could not load cart");
    const items = await res.json();

    if (items.length === 0) {
      wrap.innerHTML = `<p>Your cart is empty. <a href="index.html">Continue shopping</a>.</p>`;
      updateCartCount();
      return;
    }

    const total = items.reduce((sum, i) => sum + i.price * i.quantity, 0);
    const blocked = items.some((i) => i.unavailable || i.stock <= 0 || i.quantity > i.stock);

    wrap.innerHTML = `
      <div id="cartMessage" class="auth-error" role="status"></div>
      <div class="cart-list">${items.map(cartRowHtml).join("")}</div>
      <div class="cart-total">Total: ${formatPrice(total)}</div>
      ${
        blocked
          ? `<button class="btn-primary" disabled>Fix the items above to checkout</button>`
          : `<a href="checkout.html" class="btn-primary">Proceed to checkout</a>`
      }
    `;
    updateCartCount();
  } catch (err) {
    wrap.innerHTML = `<p>Couldn't load your cart.</p>`;
    console.error(err);
  }
}

async function changeQuantity(itemId, quantity) {
  try {
    const res = await fetch(`${API_BASE_URL}/cart/${itemId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
      body: JSON.stringify({ quantity }),
    });
    const data = await res.json();
    await loadCart(); // always re-sync with the server (it knows the real stock)
    if (!res.ok) showCartMessage(data.error || "Could not update quantity");
  } catch (err) {
    showCartMessage("Couldn't update the cart. Is the server running?");
  }
}

// One listener for the whole cart (works even though rows are re-drawn each time)
document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-action]");
  const row = e.target.closest(".cart-row");
  if (!btn || !row) return;

  const id = row.dataset.id;
  const input = row.querySelector(".qty-input");
  const current = parseInt(input.value, 10) || 1;

  if (btn.dataset.action === "inc") changeQuantity(id, current + 1);
  if (btn.dataset.action === "dec") changeQuantity(id, Math.max(1, current - 1));
  if (btn.dataset.action === "remove") {
    await fetch(`${API_BASE_URL}/cart/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    loadCart();
  }
});

// typing a quantity directly
document.addEventListener("change", (e) => {
  if (!e.target.classList.contains("qty-input")) return;
  const row = e.target.closest(".cart-row");
  const qty = parseInt(e.target.value, 10);
  if (!Number.isInteger(qty) || qty < 1) return loadCart(); // reset invalid input
  changeQuantity(row.dataset.id, qty);
});

document.addEventListener("DOMContentLoaded", loadCart);

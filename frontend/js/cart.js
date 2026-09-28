async function loadCart() {
  const token = getToken();
  const wrap = document.getElementById("cartWrap");

  if (!token) {
    wrap.innerHTML = `<p>Please <a href="login.html">log in</a> to view your cart.</p>`;
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/cart`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Could not load cart");
    const items = await res.json();

    if (items.length === 0) {
      wrap.innerHTML = `<p>Your cart is empty. <a href="index.html">Continue shopping</a>.</p>`;
      return;
    }

    let total = 0;
    const rows = items
      .map((item) => {
        const subtotal = item.price * item.quantity;
        total += subtotal;
        return `
          <div class="cart-row">
            <div class="cart-row-info">
              <h3>${item.product_name}</h3>
              <div class="cart-row-price">₹${item.price} x ${item.quantity} = ₹${subtotal}</div>
            </div>
            <button class="btn-remove" data-id="${item._id}">Remove</button>
          </div>
        `;
      })
      .join("");

    wrap.innerHTML = `
      <div class="cart-list">${rows}</div>
      <div class="cart-total">Total: ₹${total}</div>
      <a href="checkout.html" class="btn-primary">Proceed to checkout</a>
    `;

    document.querySelectorAll(".btn-remove").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-id");
        await fetch(`${API_BASE_URL}/cart/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
        loadCart(); // refresh the list after removing
      });
    });
  } catch (err) {
    wrap.innerHTML = `<p>Couldn't load your cart.</p>`;
    console.error(err);
  }
}

document.addEventListener("DOMContentLoaded", loadCart);
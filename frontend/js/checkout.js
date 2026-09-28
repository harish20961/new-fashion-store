async function loadCheckoutSummary() {
  const token = getToken();
  const summaryWrap = document.getElementById("checkoutSummary");
  const form = document.getElementById("checkoutForm");

  if (!token) {
    summaryWrap.innerHTML = `<p>Please <a href="login.html">log in</a> to checkout.</p>`;
    form.style.display = "none";
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/cart`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const items = await res.json();

    if (items.length === 0) {
      summaryWrap.innerHTML = `<p>Your cart is empty. <a href="index.html">Continue shopping</a>.</p>`;
      form.style.display = "none";
      return;
    }

    let total = 0;
    const rows = items
      .map((item) => {
        const subtotal = item.price * item.quantity;
        total += subtotal;
        return `<div class="summary-row"><span>${item.product_name} x ${item.quantity}</span><span>₹${subtotal}</span></div>`;
      })
      .join("");

    summaryWrap.innerHTML = `
      <div class="summary-rows">${rows}</div>
      <div class="summary-total"><span>Total</span><span>₹${total}</span></div>
    `;
  } catch (err) {
    summaryWrap.innerHTML = `<p>Couldn't load your cart.</p>`;
    console.error(err);
  }
}

const checkoutForm = document.getElementById("checkoutForm");
if (checkoutForm) {
  checkoutForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const token = getToken();
    const errorBox = document.getElementById("checkoutError");
    errorBox.textContent = "";

    const delivery_address = {
      full_name: document.getElementById("full_name").value.trim(),
      phone: document.getElementById("phone").value.trim(),
      line1: document.getElementById("line1").value.trim(),
      city: document.getElementById("city").value.trim(),
      pincode: document.getElementById("pincode").value.trim(),
    };

    try {
      const res = await fetch(`${API_BASE_URL}/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ delivery_address }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Could not place order");

      window.location.href = `order-confirmation.html?order_id=${data.order_id}`;
    } catch (err) {
      errorBox.textContent = err.message;
    }
  });
}

document.addEventListener("DOMContentLoaded", loadCheckoutSummary);
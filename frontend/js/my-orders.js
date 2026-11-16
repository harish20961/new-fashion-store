// Customer's order history with a status progress bar.
const STEPS = ["Placed", "Processing", "Shipped", "Delivered"];
const STEP_LABELS = {
  Placed: "Order placed",
  Processing: "Packing",
  Shipped: "Shipped",
  Delivered: "Delivered",
};

function renderProgress(status) {
  if (status === "Cancelled") {
    return `<div class="cancelled-note">This order was cancelled.</div>`;
  }
  const current = Math.max(STEPS.indexOf(status), 0);
  return `<div class="progress">${STEPS.map((step, i) => {
    const cls = i <= current ? "done" : "";
    const now = i === current ? " current" : "";
    return `<div class="progress-step ${cls}${now}">${STEP_LABELS[step]}</div>`;
  }).join("")}</div>`;
}

function renderOrder(order) {
  const date = order.created_at
    ? new Date(order.created_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })
    : "";
  const items = (order.items || []).map((item) => {
    const variant = [item.size ? `Size ${esc(item.size)}` : "", item.color ? esc(item.color) : ""]
      .filter(Boolean).join(" · ");
    const img = item.image_url ? `<img src="${esc(item.image_url)}" alt="" loading="lazy">` : "";
    return `<div class="order-item">${img}
      <div>
        <div>${esc(item.product_name)}</div>
        <small>Qty ${item.quantity}${variant ? " · " + variant : ""} · ${formatPrice(item.price)}</small>
      </div></div>`;
  }).join("");

  const a = order.delivery_address || {};
  const address = [a.full_name, a.line1, a.city, a.pincode].filter(Boolean).map(esc).join(", ");

  return `<article class="order-card">
    <div class="order-head">
      <div><strong>Order #${esc(order._id.slice(-6).toUpperCase())}</strong><small>${esc(date)}</small></div>
      <div class="order-total">${formatPrice(order.total_amount)}</div>
    </div>
    <div class="order-items">${items}</div>
    ${renderProgress(order.status)}
    ${address ? `<div class="order-address">Delivering to: ${address}</div>` : ""}
  </article>`;
}

async function loadMyOrders() {
  const message = document.getElementById("ordersMessage");
  const list = document.getElementById("ordersList");
  const token = getToken();

  if (!token) {
    message.innerHTML = `Please <a href="login.html">log in</a> to see your orders.`;
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/orders`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.status === 401) {
      localStorage.removeItem("fh_token");
      message.innerHTML = `Your session has expired. Please <a href="login.html">log in</a> again.`;
      return;
    }
    const orders = await res.json();
    if (!res.ok) throw new Error(orders.error || "Could not load orders");

    if (orders.length === 0) {
      message.innerHTML = `You have not placed any orders yet. <a href="index.html">Start shopping</a>.`;
      return;
    }
    message.style.display = "none";
    list.innerHTML = orders.map(renderOrder).join("");
  } catch (err) {
    console.error(err);
    message.textContent = "Could not load your orders. Please try again.";
  }
}

document.addEventListener("DOMContentLoaded", loadMyOrders);

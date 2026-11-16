// Orders / Users / Reviews admin pages (one script, picks the page via <body data-page>)
const token = localStorage.getItem("fh_token");
const role = localStorage.getItem("fh_role");

if (!token || role !== "admin") {
  window.location.href = "../index.html";
}

const adminNameEl = document.getElementById("adminName");
if (adminNameEl && localStorage.getItem("fh_name")) {
  adminNameEl.textContent = localStorage.getItem("fh_name");
}

document.getElementById("logoutBtn").addEventListener("click", () => {
  ["fh_token", "fh_role", "fh_name"].forEach((k) => localStorage.removeItem(k));
  window.location.href = "../index.html";
});

const tbody = document.getElementById("tableBody");
const STATUSES = ["Placed", "Processing", "Shipped", "Delivered", "Cancelled"];

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
function fmtDate(v) {
  return v ? new Date(v).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : "-";
}
function money(n) { return "₹" + Number(n || 0).toLocaleString("en-IN"); }
function empty(cols, text) {
  tbody.innerHTML = `<tr><td colspan="${cols}" class="empty-message">${text}</td></tr>`;
}
function toast(text) {
  const t = document.createElement("div");
  t.className = "toast";
  t.textContent = text;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2500);
}

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...(options.headers || {}) },
  });
  if (res.status === 401 || res.status === 403) {
    window.location.href = "../index.html";
    throw new Error("Not allowed");
  }
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

// ---------------- Orders ----------------
async function loadOrders() {
  const status = document.getElementById("statusFilter").value;
  try {
    const orders = await api("/admin/orders" + (status ? `?status=${encodeURIComponent(status)}` : ""));
    if (!orders.length) return empty(6, "No orders found");

    tbody.innerHTML = orders.map((o) => {
      const items = o.items.map((i) =>
        `${esc(i.name)} × ${i.quantity}` + (i.size ? ` (${esc(i.size)})` : "")).join("<br>");
      const a = o.address || {};
      const addr = [a.line1, a.city, a.pincode].filter(Boolean).map(esc).join(", ");
      const options = STATUSES.map((s) =>
        `<option ${s === o.status ? "selected" : ""}>${s}</option>`).join("");
      return `<tr>
        <td>#${esc(o.order_id.slice(-6).toUpperCase())}</td>
        <td>${esc(o.customer_name)}<span class="order-sub">${esc(o.customer_contact)}</span>
            <span class="order-sub">${addr}</span></td>
        <td>${items}</td>
        <td>${money(o.total_amount)}</td>
        <td><select class="status-select" data-id="${esc(o.order_id)}" data-prev="${esc(o.status)}">${options}</select></td>
        <td>${esc(fmtDate(o.created_at))}</td>
      </tr>`;
    }).join("");
  } catch (err) {
    console.error(err);
    empty(6, "Could not load orders");
  }
}

async function changeStatus(select) {
  const newStatus = select.value;
  if (newStatus === "Cancelled" && !confirm("Cancel this order? Stock will be added back.")) {
    select.value = select.dataset.prev;
    return;
  }
  try {
    await api(`/orders/${select.dataset.id}/status`, {
      method: "PUT", body: JSON.stringify({ status: newStatus }),
    });
    select.dataset.prev = newStatus;
    toast("Status updated to " + newStatus);
  } catch (err) {
    select.value = select.dataset.prev;
    toast(err.message);
  }
}

// ---------------- Users ----------------
let allUsers = [];
function renderUsers(list) {
  if (!list.length) return empty(6, "No users found");
  tbody.innerHTML = list.map((u) => `<tr>
    <td>${esc(u.name)}</td>
    <td>${esc(u.email || "-")}</td>
    <td>${esc(u.phone || "-")}</td>
    <td><span class="role-badge ${u.role === "admin" ? "admin" : ""}">${esc(u.role)}</span></td>
    <td>${u.orders}</td>
    <td>${esc(fmtDate(u.created_at))}</td>
  </tr>`).join("");
}
async function loadUsers() {
  try {
    allUsers = await api("/admin/users");
    renderUsers(allUsers);
  } catch (err) { console.error(err); empty(6, "Could not load users"); }
}

// ---------------- Reviews ----------------
async function loadReviews() {
  try {
    const reviews = await api("/admin/reviews");
    if (!reviews.length) return empty(6, "No reviews yet");
    tbody.innerHTML = reviews.map((r) => {
      const n = Math.round(r.rating || 0);
      return `<tr>
        <td>${esc(r.product_name)}</td>
        <td>${esc(r.reviewer_name)}</td>
        <td><span class="stars">${"★".repeat(n)}${"☆".repeat(5 - n)}</span></td>
        <td>${esc(r.comment || "-")}</td>
        <td>${esc(fmtDate(r.created_at))}</td>
        <td><button class="delete-btn" data-id="${esc(r.review_id)}">Delete</button></td>
      </tr>`;
    }).join("");
  } catch (err) { console.error(err); empty(6, "Could not load reviews"); }
}

// ---------------- Wiring ----------------
const page = document.body.dataset.page;

if (page === "orders") {
  document.getElementById("statusFilter").addEventListener("change", loadOrders);
  tbody.addEventListener("change", (e) => {
    if (e.target.classList.contains("status-select")) changeStatus(e.target);
  });
  loadOrders();
} else if (page === "users") {
  document.getElementById("searchBox").addEventListener("input", (e) => {
    const q = e.target.value.trim().toLowerCase();
    renderUsers(allUsers.filter((u) =>
      [u.name, u.email, u.phone].some((v) => (v || "").toLowerCase().includes(q))));
  });
  loadUsers();
} else if (page === "reviews") {
  tbody.addEventListener("click", async (e) => {
    const btn = e.target.closest(".delete-btn");
    if (!btn || !confirm("Delete this review?")) return;
    try {
      await api(`/admin/reviews/${btn.dataset.id}`, { method: "DELETE" });
      toast("Review deleted");
      loadReviews();
    } catch (err) { toast(err.message); }
  });
  loadReviews();
}

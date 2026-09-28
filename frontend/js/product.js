async function loadProductDetail() {
  const wrap = document.getElementById("productDetailWrap");
  const params = new URLSearchParams(window.location.search);
  const productId = params.get("id");

  if (!productId) {
    wrap.innerHTML = "<p>No product selected.</p>";
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/products/${productId}`);
    if (!res.ok) throw new Error("Product not found");
    const product = await res.json();

    wrap.innerHTML = `
      <div class="product-detail-grid">
        <div class="product-detail-image">${product.image_url ? `<img src="${product.image_url}" alt="${product.name}">` : ""}</div>
        <div class="product-detail-info">
          <h1>${product.name}</h1>
          <div class="product-detail-price">₹${product.price}</div>
          <div class="product-detail-category">${product.category}</div>

          <div class="qty-row">
            <label for="qty">Quantity</label>
            <input type="number" id="qty" value="1" min="1">
          </div>

          <button id="addToCartBtn" class="btn-primary btn-full">Add to cart</button>
          <p id="cartMessage" class="auth-success"></p>
        </div>
      </div>
    `;

    document.getElementById("addToCartBtn").addEventListener("click", async () => {
      const token = getToken();
      const messageBox = document.getElementById("cartMessage");

      if (!token) {
        messageBox.className = "auth-error";
        messageBox.textContent = "Please log in first.";
        setTimeout(() => (window.location.href = "login.html"), 1200);
        return;
      }

      const quantity = parseInt(document.getElementById("qty").value, 10) || 1;

      try {
        const res = await fetch(`${API_BASE_URL}/cart`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ product_id: productId, quantity }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Could not add to cart");

        messageBox.className = "auth-success";
        messageBox.textContent = "Added to cart!";
      } catch (err) {
        messageBox.className = "auth-error";
        messageBox.textContent = err.message;
      }
    });
  } catch (err) {
    wrap.innerHTML = `<p>Couldn't load this product.</p>`;
    console.error(err);
  }
}

document.addEventListener("DOMContentLoaded", loadProductDetail);
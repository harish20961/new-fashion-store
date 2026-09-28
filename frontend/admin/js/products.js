// =========================================
// FashionHub Admin - Products
// =========================================

const API_BASE_URL = "http://127.0.0.1:5000/api";

const token = localStorage.getItem("fh_token");
const role = localStorage.getItem("fh_role");


// =========================================
// Admin Check
// =========================================

if (!token || role !== "admin") {
    window.location.href = "../index.html";
}


// =========================================
// Elements
// =========================================

const productsTable = document.getElementById("productsTable");
const productCount = document.getElementById("productCount");

const searchInput = document.getElementById("searchInput");
const categoryFilter = document.getElementById("categoryFilter");

const productModal = document.getElementById("productModal");
const addProductBtn = document.getElementById("addProductBtn");
const closeModal = document.getElementById("closeModal");
const cancelBtn = document.getElementById("cancelBtn");

const productForm = document.getElementById("productForm");


// =========================================
// Load Products
// =========================================

async function loadProducts() {

    try {

        const search = searchInput.value.trim();
        const category = categoryFilter.value;

        let url = `${API_BASE_URL}/products?`;

        if (search) {
            url += `search=${encodeURIComponent(search)}&`;
        }

        if (category) {
            url += `category=${encodeURIComponent(category)}`;
        }


        const response = await fetch(url);

        const products = await response.json();


        if (!response.ok) {
            throw new Error(products.error || "Failed to load products");
        }


        displayProducts(products);

    } catch (error) {

        console.error("Products error:", error);

        productsTable.innerHTML = `
            <tr>
                <td colspan="5" class="empty-message">
                    Failed to load products
                </td>
            </tr>
        `;

        productCount.textContent = "Unable to load products";
    }
}


// =========================================
// Display Products
// =========================================

function displayProducts(products) {

    productCount.textContent =
        `${products.length} product${products.length !== 1 ? "s" : ""}`;


    if (products.length === 0) {

        productsTable.innerHTML = `
            <tr>
                <td colspan="5" class="empty-message">
                    No products found
                </td>
            </tr>
        `;

        return;
    }


    productsTable.innerHTML = products.map(product => {

        const image = product.image
    ? `../${product.image}`
    : (product.image_url || "");

        const stock = product.stock ?? 0;

        let stockClass = "stock-good";

        if (stock === 0) {
            stockClass = "stock-out";
        } else if (stock <= 5) {
            stockClass = "stock-low";
        }


        return `
            <tr>

                <td>
                    <div class="product-info">

                        ${
                            image
                            ? `<img src="${image}" alt="${escapeHTML(product.name)}">`
                            : `<div class="product-placeholder">📦</div>`
                        }

                        <div>
                            <strong>
                                ${escapeHTML(product.name || "Unnamed Product")}
                            </strong>

                            <small>
                                ${product._id}
                            </small>
                        </div>

                    </div>
                </td>


                <td>
                    ${escapeHTML(product.category || "-")}
                </td>


                <td>
                    ₹${Number(product.price || 0).toFixed(2)}
                </td>


                <td>
                    <span class="${stockClass}">
                        ${stock}
                    </span>
                </td>


                <td>

                    <div class="action-buttons">

                        <button
                            class="edit-btn"
                            onclick="openEditProduct('${product._id}')"
                        >
                            Edit
                        </button>

                        <button
                            class="delete-btn"
                            onclick="deleteProduct('${product._id}')"
                        >
                            Delete
                        </button>

                    </div>

                </td>

            </tr>
        `;

    }).join("");
}


// =========================================
// Open Add Product Modal
// =========================================

addProductBtn.addEventListener("click", function () {

    productForm.reset();

    document.getElementById("productId").value = "";

    document.getElementById("modalTitle").textContent =
        "Add Product";

    productModal.classList.add("show");

});


// =========================================
// Close Modal
// =========================================

function closeProductModal() {
    productModal.classList.remove("show");
}

closeModal.addEventListener("click", closeProductModal);

cancelBtn.addEventListener("click", closeProductModal);


// =========================================
// Add / Update Product
// =========================================

productForm.addEventListener("submit", async function (event) {

    event.preventDefault();


    const productId =
        document.getElementById("productId").value;


    const productData = {

        name: document.getElementById("productName").value.trim(),

        price: Number(
            document.getElementById("productPrice").value
        ),

        stock: Number(
            document.getElementById("productStock").value
        ),

        category:
            document.getElementById("productCategory").value,

        description:
            document.getElementById("productDescription").value.trim(),

        image:
            document.getElementById("productImage").value.trim()
    };


    try {

        let url = `${API_BASE_URL}/products`;
        let method = "POST";


        // Edit product

        if (productId) {

            url = `${API_BASE_URL}/products/${productId}`;
            method = "PUT";
        }


        const response = await fetch(url, {

            method: method,

            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },

            body: JSON.stringify(productData)

        });


        const result = await response.json();


        if (!response.ok) {
            throw new Error(
                result.error || "Failed to save product"
            );
        }


        alert(
            productId
            ? "Product updated successfully!"
            : "Product created successfully!"
        );


        closeProductModal();

        loadProducts();


    } catch (error) {

        console.error("Save product error:", error);

        alert(error.message);

    }

});


// =========================================
// Open Edit Product
// =========================================

async function openEditProduct(productId) {

    try {

        const response = await fetch(
            `${API_BASE_URL}/products/${productId}`
        );


        const product = await response.json();


        if (!response.ok) {
            throw new Error(
                product.error || "Failed to load product"
            );
        }


        document.getElementById("productId").value =
            product._id;

        document.getElementById("productName").value =
            product.name || "";

        document.getElementById("productPrice").value =
            product.price || 0;

        document.getElementById("productStock").value =
            product.stock ?? 0;

        document.getElementById("productCategory").value =
            product.category || "";

        document.getElementById("productDescription").value =
            product.description || "";

        document.getElementById("productImage").value =
            product.image || product.image_url || "";


        document.getElementById("modalTitle").textContent =
            "Edit Product";


        productModal.classList.add("show");


    } catch (error) {

        console.error("Edit product error:", error);

        alert(error.message);

    }
}


// =========================================
// Delete Product
// =========================================

async function deleteProduct(productId) {

    const confirmed = confirm(
        "Are you sure you want to delete this product?"
    );


    if (!confirmed) {
        return;
    }


    try {

        const response = await fetch(
            `${API_BASE_URL}/products/${productId}`,
            {
                method: "DELETE",

                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );


        const result = await response.json();


        if (!response.ok) {
            throw new Error(
                result.error || "Failed to delete product"
            );
        }


        alert("Product deleted successfully!");

        loadProducts();


    } catch (error) {

        console.error("Delete product error:", error);

        alert(error.message);

    }
}


// =========================================
// Search
// =========================================

let searchTimeout;

searchInput.addEventListener("input", function () {

    clearTimeout(searchTimeout);

    searchTimeout = setTimeout(() => {
        loadProducts();
    }, 400);

});


// =========================================
// Category Filter
// =========================================

categoryFilter.addEventListener("change", function () {

    loadProducts();

});


// =========================================
// Logout
// =========================================

const logoutBtn = document.getElementById("logoutBtn");

logoutBtn.addEventListener("click", function () {

    localStorage.removeItem("fh_token");
    localStorage.removeItem("fh_role");
    localStorage.removeItem("fh_name");

    window.location.href = "../index.html";

});


// =========================================
// Escape HTML
// =========================================

function escapeHTML(value) {

    const div = document.createElement("div");

    div.textContent = value;

    return div.innerHTML;
}


// =========================================
// Start
// =========================================

loadProducts();
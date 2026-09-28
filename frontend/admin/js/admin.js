// =========================================
// FashionHub Admin Dashboard
// =========================================

const API_BASE_URL = "http://127.0.0.1:5000/api";


// =========================================
// Check Admin Login
// =========================================

const token = localStorage.getItem("fh_token");
const role = localStorage.getItem("fh_role");
const adminName = localStorage.getItem("fh_name");

if (!token || role !== "admin") {
    window.location.href = "../index.html";
}


// =========================================
// Show Admin Name
// =========================================

const adminNameElement = document.getElementById("adminName");

if (adminNameElement && adminName) {
    adminNameElement.textContent = adminName;
}


// =========================================
// Load Dashboard
// =========================================

async function loadDashboard() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/admin/dashboard`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to load dashboard");
        }


        // -----------------------------
        // Statistics
        // -----------------------------

        document.getElementById("totalUsers").textContent =
            data.total_users;

        document.getElementById("totalProducts").textContent =
            data.total_products;

        document.getElementById("totalOrders").textContent =
            data.total_orders;


        // -----------------------------
        // Recent Orders
        // -----------------------------

        displayRecentOrders(data.recent_orders);


    } catch (error) {

        console.error("Dashboard error:", error);

        document.getElementById("totalUsers").textContent = "-";
        document.getElementById("totalProducts").textContent = "-";
        document.getElementById("totalOrders").textContent = "-";

    }
}


// =========================================
// Display Recent Orders
// =========================================

function displayRecentOrders(orders) {

    const ordersTable = document.getElementById("ordersTable");

    if (!ordersTable) {
        return;
    }


    // No orders

    if (!orders || orders.length === 0) {

        ordersTable.innerHTML = `
            <tr>
                <td colspan="5" class="empty-message">
                    No orders available
                </td>
            </tr>
        `;

        return;
    }


    // Create table rows

    ordersTable.innerHTML = orders.map(order => {

        const date = order.created_at
            ? new Date(order.created_at).toLocaleDateString("en-IN")
            : "-";


        return `
            <tr>

                <td>
                    #${order.order_id.slice(-6)}
                </td>

                <td>
                    ${order.user_id || "-"}
                </td>

                <td>
                    ₹${Number(order.total_amount || 0).toFixed(2)}
                </td>

                <td>
                    <span class="status ${getStatusClass(order.status)}">
                        ${order.status}
                    </span>
                </td>

                <td>
                    ${date}
                </td>

            </tr>
        `;

    }).join("");

}


// =========================================
// Order Status CSS Class
// =========================================

function getStatusClass(status) {

    switch (status) {

        case "Placed":
            return "status-placed";

        case "Processing":
            return "status-processing";

        case "Shipped":
            return "status-shipped";

        case "Delivered":
            return "status-delivered";

        case "Cancelled":
            return "status-cancelled";

        default:
            return "";

    }

}


// =========================================
// Logout
// =========================================

const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {

    logoutBtn.addEventListener("click", function () {

        localStorage.removeItem("fh_token");
        localStorage.removeItem("fh_role");
        localStorage.removeItem("fh_name");

        window.location.href = "../index.html";

    });

}


// =========================================
// Start Dashboard
// =========================================

loadDashboard();
// Register form handling
const registerForm = document.getElementById("registerForm");
if (registerForm) {
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("authError");
    errorBox.textContent = "";

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Registration failed");

      window.location.href = "login.html?registered=1";
    } catch (err) {
      errorBox.textContent = err.message;
    }
  });
}

// Login form handling
const loginForm = document.getElementById("loginForm");
if (loginForm) {
  const params = new URLSearchParams(window.location.search);
  if (params.get("registered")) {
    document.getElementById("authSuccess").textContent =
      "Account created — log in below.";
  }

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("authError");
    errorBox.textContent = "";

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Login failed");

      saveSession(data.token, data.name, data.role);
      window.location.href = "index.html";
    } catch (err) {
      errorBox.textContent = err.message;
    }
  });
}
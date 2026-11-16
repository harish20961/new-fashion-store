// Phone number + OTP login (Firebase sends the SMS, our backend verifies it).
(function () {
  const phoneForm = document.getElementById("phoneForm");
  if (!phoneForm || typeof firebase === "undefined") return;

  firebase.initializeApp(FIREBASE_CONFIG);
  const auth = firebase.auth();
  auth.languageCode = "en";

  const sendBtn = document.getElementById("sendOtpBtn");
  const verifyBtn = document.getElementById("verifyOtpBtn");
  const changeBtn = document.getElementById("changeNumberBtn");
  const stepPhone = document.getElementById("phoneStep");
  const stepOtp = document.getElementById("otpStep");
  const errorBox = document.getElementById("phoneError");
  const infoBox = document.getElementById("phoneInfo");

  let confirmation = null;
  let recaptcha = null;

  function showError(msg) { errorBox.textContent = msg || ""; }

  // "98765 43210" / "9876543210" / "+919876543210"  ->  "+919876543210"
  function normalisePhone(raw) {
    const digits = raw.replace(/[^\d+]/g, "");
    if (digits.startsWith("+")) return digits;
    const only = digits.replace(/^0+/, "");
    if (only.length === 10) return "+91" + only;
    if (only.length === 12 && only.startsWith("91")) return "+" + only;
    return null;
  }

  function friendlyError(err) {
    switch (err && err.code) {
      case "auth/invalid-phone-number": return "That phone number does not look right.";
      case "auth/too-many-requests": return "Too many attempts. Please wait a few minutes and try again.";
      case "auth/quota-exceeded": return "OTP limit reached for today. Please log in with email instead.";
      case "auth/invalid-verification-code": return "Wrong OTP. Please check and try again.";
      case "auth/code-expired": return "This OTP has expired. Please request a new one.";
      case "auth/captcha-check-failed": return "Security check failed. Refresh the page and try again.";
      case "auth/unauthorized-domain": return "This website address is not allowed for OTP login yet.";
      default: return (err && err.message) || "Something went wrong. Please try again.";
    }
  }

  function resetRecaptcha() {
    try { if (recaptcha) recaptcha.clear(); } catch (e) { /* ignore */ }
    recaptcha = null;
    document.getElementById("recaptchaBox").innerHTML = "";
  }

  async function sendOtp() {
    showError("");
    const phone = normalisePhone(document.getElementById("phoneNumber").value);
    if (!phone) { showError("Enter a valid 10-digit mobile number."); return; }

    sendBtn.disabled = true;
    sendBtn.textContent = "Sending...";
    try {
      resetRecaptcha();
      recaptcha = new firebase.auth.RecaptchaVerifier("recaptchaBox", { size: "invisible" });
      confirmation = await auth.signInWithPhoneNumber(phone, recaptcha);
      stepPhone.style.display = "none";
      stepOtp.style.display = "block";
      infoBox.textContent = "OTP sent to " + phone;
      document.getElementById("otpCode").focus();
    } catch (err) {
      console.error(err);
      showError(friendlyError(err));
      resetRecaptcha();
    } finally {
      sendBtn.disabled = false;
      sendBtn.textContent = "Send OTP";
    }
  }

  async function verifyOtp() {
    showError("");
    const code = document.getElementById("otpCode").value.trim();
    if (code.length < 6) { showError("Enter the 6 digit OTP."); return; }

    verifyBtn.disabled = true;
    verifyBtn.textContent = "Verifying...";
    try {
      const result = await confirmation.confirm(code);
      const idToken = await result.user.getIdToken();

      const res = await fetch(`${API_BASE_URL}/auth/phone-login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_token: idToken,
          name: document.getElementById("phoneName").value.trim(),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Login failed");

      await auth.signOut(); // our own JWT is used from here on
      saveSession(data.token, data.name, data.role);
      window.location.href = "index.html";
    } catch (err) {
      console.error(err);
      showError(friendlyError(err));
    } finally {
      verifyBtn.disabled = false;
      verifyBtn.textContent = "Verify and log in";
    }
  }

  sendBtn.addEventListener("click", sendOtp);
  verifyBtn.addEventListener("click", verifyOtp);
  phoneForm.addEventListener("submit", (e) => e.preventDefault());
  changeBtn.addEventListener("click", () => {
    stepOtp.style.display = "none";
    stepPhone.style.display = "block";
    document.getElementById("otpCode").value = "";
    showError("");
  });

  // Tabs: phone / email
  const tabPhone = document.getElementById("tabPhone");
  const tabEmail = document.getElementById("tabEmail");
  const emailForm = document.getElementById("loginForm");
  function selectTab(which) {
    const phone = which === "phone";
    phoneForm.style.display = phone ? "block" : "none";
    emailForm.style.display = phone ? "none" : "flex";
    tabPhone.classList.toggle("active", phone);
    tabEmail.classList.toggle("active", !phone);
  }
  tabPhone.addEventListener("click", () => selectTab("phone"));
  tabEmail.addEventListener("click", () => selectTab("email"));
  selectTab("phone");
})();

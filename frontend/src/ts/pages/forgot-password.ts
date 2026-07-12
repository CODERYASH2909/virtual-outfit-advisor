import { forgotPassword, resetPassword } from "../auth.js";
import { qs } from "../utils.js";
import { showToast } from "../components/toast.js";

document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");

  const requestSection = document.getElementById("request-section");
  const resetSection = document.getElementById("reset-section");

  if (token && resetSection && requestSection) {
    requestSection.classList.add("hidden");
    resetSection.classList.remove("hidden");

    qs<HTMLFormElement>("#reset-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const newPassword = qs<HTMLInputElement>("#new_password").value;
      const res = await resetPassword(token, newPassword);
      if (res.ok) {
        showToast("Password reset! Please log in.", "success");
        setTimeout(() => (window.location.href = "/pages/login.html"), 1200);
      } else {
        showToast("Could not reset password. The link may have expired.", "error");
      }
    });
    return;
  }

  qs<HTMLFormElement>("#request-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = qs<HTMLInputElement>("#email").value.trim();
    const res = await forgotPassword(email);
    if (res.ok) {
      showToast("If that email exists, a reset link has been sent.", "success");
    } else {
      showToast("Something went wrong. Please try again.", "error");
    }
  });
});

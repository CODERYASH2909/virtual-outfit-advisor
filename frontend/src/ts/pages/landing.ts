import { STORAGE_KEYS } from "../config.js";
import { login } from "../auth.js";
import { qs } from "../utils.js";
import { showToast } from "../components/toast.js";

function getErrorMessage(data: unknown): string {
  if (!data || typeof data !== "object" || !("errors" in data)) {
    return "Invalid credentials.";
  }

  const errors = (data as { errors?: { non_field_errors?: string[]; detail?: string } }).errors;
  return errors?.non_field_errors?.[0] || errors?.detail || "Invalid credentials.";
}

document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  const ctaButtons = document.querySelectorAll<HTMLAnchorElement>("[data-cta-auth]");
  if (token) {
    ctaButtons.forEach((btn) => (btn.href = "/pages/dashboard.html"));
  }

  const loginForm = document.querySelector<HTMLFormElement>("#hero-login-form");
  if (loginForm) {
    const submitBtn = loginForm.querySelector<HTMLButtonElement>("button[type='submit']");
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = qs<HTMLInputElement>("#hero-email").value.trim();
      const password = qs<HTMLInputElement>("#hero-password").value;

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Signing in...";
      }

      const res = await login(email, password);

      if (res.ok) {
        showToast("Welcome back!", "success");
        window.location.href = "/pages/dashboard.html";
      } else {
        showToast(getErrorMessage(res.data), "error");
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Sign In";
        }
      }
    });
  }
});

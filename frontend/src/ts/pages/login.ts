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
  const form = qs<HTMLFormElement>("#login-form");
  const submitBtn = qs<HTMLButtonElement>("#login-submit");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = qs<HTMLInputElement>("#email").value.trim();
    const password = qs<HTMLInputElement>("#password").value;

    submitBtn.disabled = true;
    submitBtn.textContent = "Signing in...";

    const res = await login(email, password);

    if (res.ok) {
      showToast("Welcome back!", "success");
      window.location.href = "/pages/dashboard.html";
    } else {
      showToast(getErrorMessage(res.data), "error");
      submitBtn.disabled = false;
      submitBtn.textContent = "Sign In";
    }
  });
});

import { register } from "../auth.js";
import { qs } from "../utils.js";
import { showToast } from "../components/toast.js";

document.addEventListener("DOMContentLoaded", () => {
  const form = qs<HTMLFormElement>("#register-form");
  const submitBtn = qs<HTMLButtonElement>("#register-submit");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      username: qs<HTMLInputElement>("#username").value.trim(),
      email: qs<HTMLInputElement>("#email").value.trim(),
      first_name: qs<HTMLInputElement>("#first_name").value.trim(),
      last_name: qs<HTMLInputElement>("#last_name").value.trim(),
      password: qs<HTMLInputElement>("#password").value,
      password_confirm: qs<HTMLInputElement>("#password_confirm").value,
      style_preference: qs<HTMLSelectElement>("#style_preference").value,
    };

    submitBtn.disabled = true;
    submitBtn.textContent = "Creating account...";

    const res = await register(payload);

    if (res.ok) {
      showToast("Account created! Please log in.", "success");
      setTimeout(() => (window.location.href = "/pages/login.html"), 1200);
    } else {
      const errors = res.data?.errors || {};
      const firstError = Object.values(errors)[0];
      const message = Array.isArray(firstError) ? firstError[0] : "Registration failed. Please check your details.";
      showToast(message as string, "error");
      submitBtn.disabled = false;
      submitBtn.textContent = "Create Account";
    }
  });
});

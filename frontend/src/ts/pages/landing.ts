import { STORAGE_KEYS } from "../config.js";

document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  const ctaButtons = document.querySelectorAll<HTMLAnchorElement>("[data-cta-auth]");
  if (token) {
    ctaButtons.forEach((btn) => (btn.href = "/pages/dashboard.html"));
  }
});

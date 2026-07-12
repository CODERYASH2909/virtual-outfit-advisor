import { requireAuth, getCurrentUser } from "../auth.js";
import { renderSidebar } from "../components/navbar.js";
import { apiRequest } from "../api.js";
import { qs } from "../utils.js";
import { showToast } from "../components/toast.js";
import { STORAGE_KEYS } from "../config.js";

async function loadProfile(): Promise<void> {
  const res = await apiRequest("/auth/profile/");
  if (!res.ok) return;
  const u = res.data as any;

  qs<HTMLInputElement>("#first_name").value = u.first_name || "";
  qs<HTMLInputElement>("#last_name").value = u.last_name || "";
  qs<HTMLInputElement>("#email").value = u.email || "";
  qs<HTMLInputElement>("#phone_number").value = u.phone_number || "";
  qs<HTMLInputElement>("#city").value = u.city || "";
  qs<HTMLInputElement>("#country").value = u.country || "";
  qs<HTMLSelectElement>("#gender").value = u.gender || "prefer_not_to_say";
  qs<HTMLSelectElement>("#style_preference").value = u.style_preference || "casual";
  if (u.date_of_birth) qs<HTMLInputElement>("#date_of_birth").value = u.date_of_birth;

  localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(u));
}

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();
  renderSidebar("sidebar-mount", "/pages/profile.html");
  loadProfile();

  qs<HTMLFormElement>("#profile-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("first_name", qs<HTMLInputElement>("#first_name").value);
    formData.append("last_name", qs<HTMLInputElement>("#last_name").value);
    formData.append("phone_number", qs<HTMLInputElement>("#phone_number").value);
    formData.append("city", qs<HTMLInputElement>("#city").value);
    formData.append("country", qs<HTMLInputElement>("#country").value);
    formData.append("gender", qs<HTMLSelectElement>("#gender").value);
    formData.append("style_preference", qs<HTMLSelectElement>("#style_preference").value);
    const dob = qs<HTMLInputElement>("#date_of_birth").value;
    if (dob) formData.append("date_of_birth", dob);

    const avatarInput = qs<HTMLInputElement>("#avatar");
    if (avatarInput.files && avatarInput.files[0]) {
      formData.append("avatar", avatarInput.files[0]);
    }

    const res = await apiRequest("/auth/profile/", { method: "PATCH", body: formData, isFormData: true });
    if (res.ok) {
      showToast("Profile updated.", "success");
      loadProfile();
    } else {
      showToast("Failed to update profile.", "error");
    }
  });

  qs<HTMLFormElement>("#password-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const old_password = qs<HTMLInputElement>("#old_password").value;
    const new_password = qs<HTMLInputElement>("#new_password").value;

    const res = await apiRequest("/auth/change-password/", { method: "POST", body: { old_password, new_password } });
    if (res.ok) {
      showToast("Password changed successfully.", "success");
      (e.target as HTMLFormElement).reset();
    } else {
      showToast("Failed to change password. Check your current password.", "error");
    }
  });
});

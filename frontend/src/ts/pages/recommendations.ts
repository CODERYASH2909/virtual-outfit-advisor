import { requireAuth } from "../auth.js";
import { renderSidebar } from "../components/navbar.js";
import { apiRequest } from "../api.js";
import { qs, getImageUrl } from "../utils.js";
import { showToast } from "../components/toast.js";

interface RecommendationItem {
  id: number; name: string; category: string; color: string; image: string | null;
}

interface Recommendation {
  id: number;
  items_detail: RecommendationItem[];
  occasion: string;
  season: string;
  source: string;
  notes: string;
  is_saved: boolean;
}

function renderRecommendation(rec: Recommendation): void {
  const container = qs<HTMLElement>("#recommendation-result");
  container.innerHTML = `
    <div class="card">
      <div class="mb-4 flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-ink-900">Your Outfit Suggestion</h3>
          <p class="text-xs capitalize text-gray-500">${rec.source} &middot; ${rec.season.replace("_", " ")}</p>
        </div>
        <button id="save-rec-btn" class="btn-secondary text-xs !py-2">Save to Favorites</button>
      </div>
      <div class="mb-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
        ${rec.items_detail.map((item) => `
          <div class="rounded-lg border border-gray-100 p-3 text-center">
            <div class="mb-2 h-40 w-full overflow-hidden rounded-md bg-voa-50">
              ${item.image ? `<img src="${getImageUrl(item.image)}" class="h-full w-full object-cover" />` : `<div class="flex h-full items-center justify-center text-xs text-voa-300">No Image</div>`}
            </div>
            <p class="truncate text-xs font-medium">${item.name}</p>
          </div>`).join("")}
      </div>
      <p class="text-sm text-gray-600">${rec.notes}</p>
    </div>
  `;

  qs<HTMLButtonElement>("#save-rec-btn").addEventListener("click", async () => {
    const res = await apiRequest(`/recommendations/history/${rec.id}/save/`, { method: "POST" });
    if (res.ok) {
      const res2 = await apiRequest("/favorites/", { method: "POST", body: { recommendation: rec.id } });
      if (res2.ok) showToast("Saved to Favorites!", "success");
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();
  renderSidebar("sidebar-mount", "/pages/recommendations.html");

  let detectedLat: number | null = null;
  let detectedLon: number | null = null;

  const cityInput = qs<HTMLInputElement>("#rec-city");
  const detectLocBtn = qs<HTMLButtonElement>("#detect-loc-btn");

  cityInput.addEventListener("input", () => {
    if (detectedLat !== null || detectedLon !== null) {
      detectedLat = null;
      detectedLon = null;
      if (cityInput.value === "Detected Location") {
        cityInput.value = "";
      }
    }
  });

  detectLocBtn.addEventListener("click", () => {
    if (!navigator.geolocation) {
      showToast("Geolocation is not supported by your browser.", "error");
      return;
    }

    detectLocBtn.disabled = true;
    detectLocBtn.classList.add("animate-pulse");
    const originalPlaceholder = cityInput.placeholder;
    cityInput.placeholder = "Locating...";

    navigator.geolocation.getCurrentPosition(
      (position) => {
        detectedLat = position.coords.latitude;
        detectedLon = position.coords.longitude;
        cityInput.value = "Detected Location";
        detectLocBtn.disabled = false;
        detectLocBtn.classList.remove("animate-pulse");
        cityInput.placeholder = originalPlaceholder;
        showToast("Location detected successfully!", "success");
      },
      (error) => {
        detectLocBtn.disabled = false;
        detectLocBtn.classList.remove("animate-pulse");
        cityInput.placeholder = originalPlaceholder;
        let errMsg = "Unable to retrieve location.";
        if (error.code === error.PERMISSION_DENIED) {
          errMsg = "Location permission denied.";
        }
        showToast(errMsg, "error");
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  });

  qs<HTMLFormElement>("#recommend-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const season = qs<HTMLSelectElement>("#rec-season").value;
    const occasion = qs<HTMLSelectElement>("#rec-occasion").value;
    const city = cityInput.value.trim();
    const country = qs<HTMLSelectElement>("#rec-country").value;

    const btn = qs<HTMLButtonElement>("#generate-btn");
    btn.disabled = true;
    btn.textContent = (detectedLat !== null && detectedLon !== null) || city ? "Checking Weather..." : "Generating...";

    const res = await apiRequest<{ success: boolean; recommendation?: Recommendation; message?: string }>(
      "/recommendations/generate/",
      {
        method: "POST",
        body: {
          season,
          occasion,
          city: city === "Detected Location" ? "" : city,
          country: city === "Detected Location" ? "" : country,
          latitude: detectedLat,
          longitude: detectedLon
        }
      }
    );

    btn.disabled = false;
    btn.textContent = "Generate Outfit";

    if (res.ok && res.data.recommendation) {
      renderRecommendation(res.data.recommendation);
    } else {
      showToast(res.data.message || "Could not generate a recommendation. Add more wardrobe items.", "error");
    }
  });
});

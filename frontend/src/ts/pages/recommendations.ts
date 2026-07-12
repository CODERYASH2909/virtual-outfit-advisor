import { requireAuth } from "../auth.js";
import { renderSidebar } from "../components/navbar.js";
import { apiRequest } from "../api.js";
import { qs } from "../utils.js";
import { showToast } from "../components/toast.js";

interface RecommendationItem {
  id: number; name: string; category: string; color: string; image: string | null;
}

interface Recommendation {
  id: number;
  items_detail: RecommendationItem[];
  occasion: string;
  season: string;
  notes: string;
  is_saved: boolean;
}

function renderRecommendation(rec: Recommendation): void {
  const container = qs<HTMLElement>("#recommendation-result");
  container.innerHTML = `
    <div class="card">
      <div class="mb-4 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-ink-900">Your Outfit Suggestion</h3>
        <button id="save-rec-btn" class="btn-secondary text-xs !py-2">Save to Favorites</button>
      </div>
      <div class="mb-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
        ${rec.items_detail.map((item) => `
          <div class="rounded-lg border border-gray-100 p-3 text-center">
            <div class="mb-2 h-20 w-full overflow-hidden rounded-md bg-voa-50">
              ${item.image ? `<img src="${item.image}" class="h-full w-full object-cover" />` : `<div class="flex h-full items-center justify-center text-xs text-voa-300">No Image</div>`}
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

  qs<HTMLFormElement>("#recommend-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const season = qs<HTMLSelectElement>("#rec-season").value;
    const occasion = qs<HTMLSelectElement>("#rec-occasion").value;

    const btn = qs<HTMLButtonElement>("#generate-btn");
    btn.disabled = true;
    btn.textContent = "Generating...";

    const res = await apiRequest<{ success: boolean; recommendation?: Recommendation; message?: string }>(
      "/recommendations/generate/",
      { method: "POST", body: { season, occasion } }
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

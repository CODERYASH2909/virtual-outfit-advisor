import { requireAuth } from "../auth.js";
import { renderSidebar } from "../components/navbar.js";
import { apiRequest } from "../api.js";
import { qs, qsa } from "../utils.js";
import { showToast } from "../components/toast.js";

interface FavoriteEntry {
  id: number;
  outfit_detail: { id: number; name: string; items_detail: any[] } | null;
  recommendation_detail: { id: number; items_detail: any[]; occasion: string; season: string } | null;
  created_at: string;
}

async function loadFavorites(): Promise<void> {
  const res = await apiRequest<{ results: FavoriteEntry[] }>("/favorites/");
  const grid = qs<HTMLElement>("#favorites-grid");

  if (!res.ok) {
    grid.innerHTML = `<p class="col-span-full text-sm text-rose-600">Failed to load favorites.</p>`;
    return;
  }

  const favorites = res.data.results || [];
  grid.innerHTML = favorites.length
    ? favorites.map((fav) => {
        const target = fav.outfit_detail || fav.recommendation_detail;
        const items = target?.items_detail || [];
        const title = fav.outfit_detail ? fav.outfit_detail.name : `${fav.recommendation_detail?.occasion} outfit`;
        return `
        <div class="card">
          <div class="mb-3 flex items-center justify-between">
            <h3 class="font-semibold capitalize text-ink-900">${title}</h3>
            <button data-remove-id="${fav.id}" class="text-xs text-rose-600 hover:underline">Remove</button>
          </div>
          <div class="grid grid-cols-3 gap-2">
            ${items.map((item: any) => `
              <div class="h-16 overflow-hidden rounded bg-voa-50">
                ${item.image ? `<img src="${item.image}" class="h-full w-full object-cover" />` : ""}
              </div>`).join("")}
          </div>
        </div>`;
      }).join("")
    : `<p class="col-span-full text-sm text-gray-500">No favorites saved yet. Generate a recommendation and save it here!</p>`;

  qsa<HTMLButtonElement>("[data-remove-id]", grid).forEach((btn) =>
    btn.addEventListener("click", async () => {
      const res = await apiRequest(`/favorites/${btn.dataset.removeId}/`, { method: "DELETE" });
      if (res.ok) {
        showToast("Removed from favorites.", "success");
        loadFavorites();
      }
    })
  );
}

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();
  renderSidebar("sidebar-mount", "/pages/favorites.html");
  loadFavorites();
});

import { requireAuth, getCurrentUser } from "../auth.js";
import { renderSidebar } from "../components/navbar.js";
import { apiRequest } from "../api.js";
import { qs, getImageUrl } from "../utils.js";
 
interface WardrobeStats {
  total_items: number;
  favorites: number;
  by_category: Record<string, number>;
  never_worn: number;
}

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  renderSidebar("sidebar-mount", "/pages/dashboard.html");

  const user = getCurrentUser();
  if (user) {
    qs<HTMLElement>("#welcome-name").textContent = user.first_name || user.username;
  }

  const statsRes = await apiRequest<WardrobeStats>("/wardrobe/items/stats/");
  if (statsRes.ok) {
    qs<HTMLElement>("#stat-total").textContent = String(statsRes.data.total_items);
    qs<HTMLElement>("#stat-favorites").textContent = String(statsRes.data.favorites);
    qs<HTMLElement>("#stat-never-worn").textContent = String(statsRes.data.never_worn);
  }

  const recentRes = await apiRequest<{ results: any[] }>("/wardrobe/items/?ordering=-created_at&page_size=4");
  if (recentRes.ok) {
    const container = qs<HTMLElement>("#recent-items");
    const items = recentRes.data.results || [];
    container.innerHTML = items.length
      ? items.map((item) => `
        <div class="card flex items-center gap-4">
          <div class="h-14 w-14 flex-shrink-0 overflow-hidden rounded-lg bg-voa-50">
            ${item.image ? `<img src="${getImageUrl(item.image)}" class="h-full w-full object-cover" alt="${item.name}" />` : `<div class="flex h-full items-center justify-center text-voa-400 text-xs">No image</div>`}
          </div>
          <div class="min-w-0">
            <p class="truncate font-medium text-ink-900">${item.name}</p>
            <p class="text-xs text-gray-500">${item.category_display} &middot; ${item.color}</p>
          </div>
        </div>`).join("")
      : `<p class="text-sm text-gray-500 col-span-full">No wardrobe items yet. Start by adding a few pieces!</p>`;
  }

  qs<HTMLElement>("#quick-generate-btn").addEventListener("click", () => {
    window.location.href = "/pages/recommendations.html";
  });
});

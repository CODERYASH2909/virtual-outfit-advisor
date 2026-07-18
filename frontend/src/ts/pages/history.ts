import { requireAuth } from "../auth.js";
import { renderSidebar } from "../components/navbar.js";
import { apiRequest } from "../api.js";
import { qs, qsa, formatDate, buildQueryString, getImageUrl } from "../utils.js";
import { showToast } from "../components/toast.js";

interface HistoryEntry {
  id: number;
  items_detail: any[];
  occasion: string;
  season: string;
  source: string;
  notes: string;
  is_saved: boolean;
  created_at: string;
}

let filters: Record<string, string> = {};

async function loadHistory(): Promise<void> {
  const res = await apiRequest<{ results: HistoryEntry[] }>(`/recommendations/history/${buildQueryString(filters)}`);
  const list = qs<HTMLElement>("#history-list");

  if (!res.ok) {
    list.innerHTML = `<p class="text-sm text-rose-600">Failed to load history.</p>`;
    return;
  }

  const entries = res.data.results || [];
  list.innerHTML = entries.length
    ? entries.map((entry) => `
      <div class="card flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="flex -space-x-3">
            ${entry.items_detail.slice(0, 3).map((item: any) => `
              <div class="h-10 w-10 overflow-hidden rounded-full border-2 border-white bg-voa-50">
                ${item.image ? `<img src="${getImageUrl(item.image)}" class="h-full w-full object-cover" />` : ""}
              </div>`).join("")}
          </div>
          <div>
            <p class="font-medium capitalize text-ink-900">${entry.occasion} &middot; ${entry.season.replace("_", " ")}</p>
            <p class="text-xs text-gray-500">${formatDate(entry.created_at)} &middot; ${entry.source}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          ${entry.is_saved ? `<span class="badge">Saved</span>` : ""}
          <button data-delete-id="${entry.id}" class="text-xs text-rose-600 hover:underline">Delete</button>
        </div>
      </div>`).join("")
    : `<p class="text-sm text-gray-500">No recommendation history yet.</p>`;

  qsa<HTMLButtonElement>("[data-delete-id]", list).forEach((btn) =>
    btn.addEventListener("click", async () => {
      const res = await apiRequest(`/recommendations/history/${btn.dataset.deleteId}/delete/`, { method: "DELETE" });
      if (res.ok) {
        showToast("Entry deleted.", "success");
        loadHistory();
      }
    })
  );
}

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();
  renderSidebar("sidebar-mount", "/pages/history.html");

  qsa<HTMLSelectElement>("[data-filter]").forEach((select) =>
    select.addEventListener("change", () => {
      const key = select.dataset.filter!;
      if (select.value) filters[key] = select.value;
      else delete filters[key];
      loadHistory();
    })
  );

  loadHistory();
});

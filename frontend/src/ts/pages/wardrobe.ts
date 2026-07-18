import { requireAuth } from "../auth.js";
import { renderSidebar } from "../components/navbar.js";
import { apiRequest } from "../api.js";
import { qs, qsa, debounce, buildQueryString, getImageUrl } from "../utils.js";
import { showToast } from "../components/toast.js";
import { openModal, closeModal, bindModalDismiss } from "../components/modal.js";

interface WardrobeItem {
  id: number; name: string; category: string; category_display: string;
  color: string; season: string; season_display: string; occasion: string;
  occasion_display: string; brand: string; image: string | null;
  is_favorite: boolean; times_worn: number; notes: string; tags: string;
}

let currentFilters: Record<string, string> = {};
let editingItemId: number | null = null;

async function loadItems(): Promise<void> {
  const query = buildQueryString({ ...currentFilters });
  const res = await apiRequest<{ results: WardrobeItem[] }>(`/wardrobe/items/${query}`);
  const grid = qs<HTMLElement>("#wardrobe-grid");

  if (!res.ok) {
    grid.innerHTML = `<p class="col-span-full text-sm text-rose-600">Failed to load wardrobe items.</p>`;
    return;
  }

  const items = res.data.results || [];
  grid.innerHTML = items.length
    ? items.map(renderItemCard).join("")
    : `<p class="col-span-full text-sm text-gray-500">No items match your filters. Try adjusting search or add a new item.</p>`;

  qsa<HTMLButtonElement>("[data-edit-id]", grid).forEach((btn) =>
    btn.addEventListener("click", () => openEditModal(items.find((i) => i.id === Number(btn.dataset.editId))!))
  );
  qsa<HTMLButtonElement>("[data-delete-id]", grid).forEach((btn) =>
    btn.addEventListener("click", () => deleteItem(Number(btn.dataset.deleteId)))
  );
  qsa<HTMLButtonElement>("[data-fav-id]", grid).forEach((btn) =>
    btn.addEventListener("click", () => toggleFavorite(Number(btn.dataset.favId)))
  );
}

function renderItemCard(item: WardrobeItem): string {
  return `
  <div class="card group relative flex flex-col">
    <button data-fav-id="${item.id}" class="absolute right-4 top-4 z-10 rounded-full bg-white/90 p-2 shadow-sm transition hover:scale-110">
      <span class="${item.is_favorite ? "text-rose-500" : "text-gray-300"}">&#9829;</span>
    </button>
    <div class="mb-4 h-40 w-full overflow-hidden rounded-lg bg-voa-50">
      ${item.image ? `<img src="${getImageUrl(item.image)}" class="h-full w-full object-cover" alt="${item.name}" />` : `<div class="flex h-full items-center justify-center text-voa-300 text-sm">No Image</div>`}
    </div>
    <h3 class="font-semibold text-ink-900">${item.name}</h3>
    <p class="text-xs text-gray-500 mb-2">${item.brand || "No brand"}</p>
    <div class="mb-4 flex flex-wrap gap-1.5">
      <span class="badge">${item.category_display}</span>
      <span class="badge">${item.color}</span>
      <span class="badge">${item.season_display}</span>
    </div>
    <div class="mt-auto flex gap-2">
      <button data-edit-id="${item.id}" class="btn-secondary flex-1 !py-2 text-xs">Edit</button>
      <button data-delete-id="${item.id}" class="btn-secondary flex-1 !py-2 text-xs text-rose-600 hover:border-rose-300">Delete</button>
    </div>
  </div>`;
}

async function toggleFavorite(id: number): Promise<void> {
  const res = await apiRequest(`/wardrobe/items/${id}/toggle_favorite/`, { method: "POST" });
  if (res.ok) loadItems();
}

async function deleteItem(id: number): Promise<void> {
  if (!confirm("Delete this wardrobe item? This cannot be undone.")) return;
  const res = await apiRequest(`/wardrobe/items/${id}/`, { method: "DELETE" });
  if (res.ok) {
    showToast("Item deleted.", "success");
    loadItems();
  } else {
    showToast("Failed to delete item.", "error");
  }
}

function openEditModal(item: WardrobeItem): void {
  editingItemId = item.id;
  qs<HTMLElement>("#item-modal-title").textContent = "Edit Item";
  qs<HTMLInputElement>("#item-name").value = item.name;
  qs<HTMLSelectElement>("#item-category").value = item.category;
  qs<HTMLInputElement>("#item-color").value = item.color;
  qs<HTMLSelectElement>("#item-season").value = item.season;
  qs<HTMLSelectElement>("#item-occasion").value = item.occasion;
  qs<HTMLInputElement>("#item-brand").value = item.brand || "";
  qs<HTMLTextAreaElement>("#item-notes").value = item.notes || "";
  qs<HTMLInputElement>("#item-tags").value = item.tags || "";
  openModal("item-modal");
}

function openAddModal(): void {
  editingItemId = null;
  qs<HTMLElement>("#item-modal-title").textContent = "Add New Item";
  qs<HTMLFormElement>("#item-form").reset();
  openModal("item-modal");
}

async function submitItemForm(e: Event): Promise<void> {
  e.preventDefault();
  const formData = new FormData();
  formData.append("name", qs<HTMLInputElement>("#item-name").value);
  formData.append("category", qs<HTMLSelectElement>("#item-category").value);
  formData.append("color", qs<HTMLInputElement>("#item-color").value);
  formData.append("season", qs<HTMLSelectElement>("#item-season").value);
  formData.append("occasion", qs<HTMLSelectElement>("#item-occasion").value);
  formData.append("brand", qs<HTMLInputElement>("#item-brand").value);
  formData.append("notes", qs<HTMLTextAreaElement>("#item-notes").value);
  formData.append("tags", qs<HTMLInputElement>("#item-tags").value);

  const fileInput = qs<HTMLInputElement>("#item-image");
  if (fileInput.files && fileInput.files[0]) {
    formData.append("image", fileInput.files[0]);
  }

  const path = editingItemId ? `/wardrobe/items/${editingItemId}/` : "/wardrobe/items/";
  const method = editingItemId ? "PATCH" : "POST";

  const res = await apiRequest(path, { method, body: formData, isFormData: true });
  if (res.ok) {
    showToast(editingItemId ? "Item updated." : "Item added.", "success");
    closeModal("item-modal");
    loadItems();
  } else {
    showToast("Failed to save item. Please check the form.", "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();
  renderSidebar("sidebar-mount", "/pages/wardrobe.html");
  bindModalDismiss("item-modal");

  qs<HTMLButtonElement>("#add-item-btn").addEventListener("click", openAddModal);
  qs<HTMLFormElement>("#item-form").addEventListener("submit", submitItemForm);

  const performSearch = () => {
    currentFilters.search = qs<HTMLInputElement>("#search-input").value;
    loadItems();
  };

  qs<HTMLButtonElement>("#search-btn").addEventListener("click", performSearch);

  qs<HTMLInputElement>("#search-input").addEventListener("keydown", (e: KeyboardEvent) => {
    if (e.key === "Enter") {
      performSearch();
    }
  });

  qs<HTMLInputElement>("#search-input").addEventListener(
    "input",
    debounce((e: Event) => {
      currentFilters.search = (e.target as HTMLInputElement).value;
      loadItems();
    }, 350)
  );

  qsa<HTMLSelectElement>("[data-filter]").forEach((select) =>
    select.addEventListener("change", () => {
      const key = select.dataset.filter!;
      if (select.value) currentFilters[key] = select.value;
      else delete currentFilters[key];
      loadItems();
    })
  );

  loadItems();
});

import { requireAuth } from "../auth.js";
import { renderSidebar } from "../components/navbar.js";
import { apiRequest } from "../api.js";
import { qs, getImageUrl } from "../utils.js";
import { showToast } from "../components/toast.js";

interface RecommendationItem {
  id: number;
  name: string;
  category: string;
  color: string;
  image: string | null;
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

interface TryOnPhoto {
  id: number;
  photo: string;
  processed_photo: string | null;
  uploaded_at: string;
}

interface TryOnResult {
  id: number;
  recommendation: number;
  result_image: string;
  created_at: string;
}

interface ProcessedItem {
  name: string;
  category: string;
  cloth_type: string;
  status: string;
}

let currentUserPhoto: TryOnPhoto | null = null;
let currentRecommendation: Recommendation | null = null;
let pendingPhotoFile: File | null = null;

function showTryOnAlert(message: string, type: "error" | "success" | "info" = "error"): void {
  const alertEl = qs<HTMLElement>("#tryon-alert");
  const textEl = qs<HTMLElement>("#tryon-alert-text");
  textEl.textContent = message;
  alertEl.className = "mb-4 px-4 py-3 rounded-xl text-xs flex items-center justify-between shadow-xs transition-all ";
  if (type === "error") {
    alertEl.className += "bg-rose-50/90 text-rose-800 border border-rose-200/80";
  } else if (type === "success") {
    alertEl.className += "bg-emerald-50/90 text-emerald-800 border border-emerald-200/80";
  } else {
    alertEl.className += "bg-voa-50/90 text-voa-900 border border-voa-200/80";
  }
  alertEl.classList.remove("hidden");
}

function hideTryOnAlert(): void {
  const alertEl = qs<HTMLElement>("#tryon-alert");
  alertEl.classList.add("hidden");
}

async function loadUserPhoto(): Promise<void> {
  const res = await apiRequest<TryOnPhoto>("/tryon/photo/");
  if (res.ok && res.data && res.data.photo) {
    currentUserPhoto = res.data;
    renderPhotoState(true);
  } else {
    currentUserPhoto = null;
    renderPhotoState(false);
  }
}

function renderPhotoState(hasPhoto: boolean): void {
  const uploadContainer = qs<HTMLElement>("#photo-upload-container");
  const displayContainer = qs<HTMLElement>("#photo-display-container");
  const pendingPreview = qs<HTMLElement>("#photo-pending-preview");

  pendingPreview.classList.add("hidden");
  pendingPhotoFile = null;

  if (hasPhoto && currentUserPhoto) {
    uploadContainer.classList.add("hidden");
    displayContainer.classList.remove("hidden");
    const currentImg = qs<HTMLImageElement>("#photo-current-img");
    const displayUrl = currentUserPhoto.processed_photo || currentUserPhoto.photo;
    currentImg.src = getImageUrl(displayUrl) || "";
  } else {
    uploadContainer.classList.remove("hidden");
    displayContainer.classList.add("hidden");
  }
}

function handlePhotoSelect(file: File): void {
  const allowed = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
  if (!allowed.includes(file.type.toLowerCase())) {
    showTryOnAlert("Please upload a valid JPG, PNG, or WEBP image.");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showTryOnAlert("Photo size must be less than 10MB.");
    return;
  }

  hideTryOnAlert();
  pendingPhotoFile = file;
  const pendingPreview = qs<HTMLElement>("#photo-pending-preview");
  const pendingImg = qs<HTMLImageElement>("#photo-pending-img");

  const reader = new FileReader();
  reader.onload = (e) => {
    pendingImg.src = e.target?.result as string;
    pendingPreview.classList.remove("hidden");
  };
  reader.readAsDataURL(file);
}

async function uploadPendingPhoto(): Promise<void> {
  if (!pendingPhotoFile) return;

  const btn = qs<HTMLButtonElement>("#photo-confirm-upload-btn");
  btn.disabled = true;
  btn.textContent = "Uploading...";

  const formData = new FormData();
  formData.append("photo", pendingPhotoFile);

  const res = await apiRequest<TryOnPhoto>("/tryon/photo/", {
    method: "POST",
    body: formData,
    isFormData: true,
  });

  btn.disabled = false;
  btn.textContent = "Upload Photo";

  if (res.ok && res.data && res.data.photo) {
    currentUserPhoto = res.data;
    renderPhotoState(true);
    showToast("Try-On photo saved!", "success");
  } else {
    const errData = res.data as any;
    const detailMsg =
      errData?.detail ||
      errData?.message ||
      errData?.errors?.detail ||
      "Failed to upload photo. Please try again.";
    showTryOnAlert(detailMsg);
  }
}

async function deleteUserPhoto(): Promise<void> {
  if (!confirm("Are you sure you want to delete your Try-On photo?")) return;

  const res = await apiRequest("/tryon/photo/", { method: "DELETE" });
  if (res.ok || res.status === 204 || res.status === 404) {
    currentUserPhoto = null;
    renderPhotoState(false);
    showToast("Photo deleted.", "info");
  } else {
    showTryOnAlert("Unable to delete photo. Please try again.");
  }
}

function setSelectedRecommendation(rec: Recommendation): void {
  currentRecommendation = rec;

  const emptyState = qs<HTMLElement>("#outfit-empty-state");
  const selectedState = qs<HTMLElement>("#outfit-selected-state");
  const summaryContainer = qs<HTMLElement>("#outfit-items-summary");

  emptyState.classList.add("hidden");
  selectedState.classList.remove("hidden");

  summaryContainer.innerHTML = `
    <div class="font-bold text-ink-900 border-b border-gray-100 pb-2 mb-2 flex items-center justify-between">
      <span class="flex items-center gap-1.5">
        <span class="h-2 w-2 rounded-full bg-voa-500"></span>
        Outfit Suggestion #${rec.id}
      </span>
      <span class="text-[10px] uppercase font-bold text-voa-800 bg-voa-50 border border-voa-200/60 px-2.5 py-0.5 rounded-full">${rec.occasion}</span>
    </div>
    <div class="space-y-2">
      ${rec.items_detail
        .map(
          (item) => `
        <div class="flex items-center justify-between text-gray-700 bg-gray-50/60 p-2 rounded-xl border border-gray-100/60">
          <div class="flex items-center gap-2">
            <span class="text-[10px] font-semibold uppercase bg-white border border-gray-200 text-gray-600 px-1.5 py-0.5 rounded-md min-w-[55px] text-center">${item.category}</span>
            <span class="font-semibold text-ink-900 text-xs">${item.name}</span>
          </div>
          <span class="text-[10px] text-gray-400 font-medium capitalize">${item.color}</span>
        </div>
      `
        )
        .join("")}
    </div>
  `;
}

async function generateVirtualTryOn(): Promise<void> {
  hideTryOnAlert();

  if (!currentUserPhoto) {
    showTryOnAlert("Please upload your photo first to use Virtual Try-On.");
    const photoSection = qs<HTMLElement>("#tryon-photo-wrapper");
    photoSection.scrollIntoView({ behavior: "smooth" });
    return;
  }

  if (!currentRecommendation) {
    showTryOnAlert("Please generate or select an outfit recommendation first.");
    return;
  }

  const outfitWrapper = qs<HTMLElement>("#tryon-outfit-wrapper");
  const loadingState = qs<HTMLElement>("#tryon-loading-state");
  const resultState = qs<HTMLElement>("#tryon-result-state");
  const statusBadge = qs<HTMLElement>("#tryon-status-badge");

  outfitWrapper.classList.add("hidden");
  resultState.classList.add("hidden");
  loadingState.classList.remove("hidden");
  statusBadge.textContent = "Processing...";
  statusBadge.className =
    "badge text-[11px] font-semibold !bg-amber-50 !text-amber-800 !border-amber-200 animate-pulse";

  const res = await apiRequest<{
    success: boolean;
    result?: TryOnResult;
    items_processed?: ProcessedItem[];
    message?: string;
  }>("/tryon/generate/", {
    method: "POST",
    body: { recommendation_id: currentRecommendation.id },
  });

  loadingState.classList.add("hidden");

  if (res.ok && res.data && res.data.success && res.data.result) {
    statusBadge.textContent = "Completed";
    statusBadge.className =
      "badge text-[11px] font-semibold !bg-emerald-50 !text-emerald-800 !border-emerald-200";

    resultState.classList.remove("hidden");
    const resultImg = qs<HTMLImageElement>("#tryon-result-img");
    resultImg.src = getImageUrl(res.data.result.result_image) || "";
    
    const applied = res.data.items_processed
      ? res.data.items_processed.filter((p: ProcessedItem) => p.status === "applied")
      : [];
    const appliedCount = applied.length || 1;
    const appliedNames = applied.map((p: ProcessedItem) => p.name).join(", ");
    showToast(
      `Virtual Try-On generated! Wearing: ${appliedNames || "outfit"}`,
      "success"
    );
  } else {
    outfitWrapper.classList.remove("hidden");
    statusBadge.textContent = "Failed";
    statusBadge.className =
      "badge text-[11px] font-semibold !bg-rose-50 !text-rose-800 !border-rose-200";

    const errMsg =
      res.data?.message ||
      "Unable to generate Virtual Try-On preview. Please try again later.";
    showTryOnAlert(errMsg);
  }
}

function handleTryAnother(): void {
  const resultState = qs<HTMLElement>("#tryon-result-state");
  const outfitWrapper = qs<HTMLElement>("#tryon-outfit-wrapper");
  const statusBadge = qs<HTMLElement>("#tryon-status-badge");

  resultState.classList.add("hidden");
  outfitWrapper.classList.remove("hidden");

  statusBadge.textContent = "Ready";
  statusBadge.className = "badge text-[11px] font-semibold";
}

function renderRecommendation(rec: Recommendation): void {
  setSelectedRecommendation(rec);

  const container = qs<HTMLElement>("#recommendation-result");
  container.innerHTML = `
    <div class="card border-2 border-voa-500/20 shadow-md">
      <div class="mb-4 flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-ink-900">Your Outfit Suggestion</h3>
          <p class="text-xs capitalize text-gray-500">${rec.source} &middot; ${rec.season.replace("_", " ")}</p>
        </div>
        <div class="flex gap-2">
          <button id="try-this-rec-btn" class="btn-primary text-xs !py-1.5 !px-3 shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            </svg>
            Try This Outfit
          </button>
          <button id="save-rec-btn" class="btn-secondary text-xs !py-1.5 !px-3">Save</button>
        </div>
      </div>
      <div class="mb-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
        ${rec.items_detail
          .map(
            (item) => `
          <div class="rounded-xl border border-gray-100 p-3 text-center bg-white shadow-xs">
            <div class="mb-2 h-36 w-full overflow-hidden rounded-lg bg-voa-50/50">
              ${
                item.image
                  ? `<img src="${getImageUrl(item.image)}" class="h-full w-full object-cover" />`
                  : `<div class="flex h-full items-center justify-center text-xs text-voa-300">No Image</div>`
              }
            </div>
            <p class="truncate text-xs font-semibold text-ink-900">${item.name}</p>
            <p class="text-[10px] text-gray-400 capitalize">${item.category} &middot; ${item.color}</p>
          </div>`
          )
          .join("")}
      </div>
      <p class="text-xs text-gray-600 bg-gray-50/70 p-3 rounded-xl border border-gray-100">${rec.notes}</p>
    </div>
  `;

  qs<HTMLButtonElement>("#save-rec-btn").addEventListener("click", async () => {
    const res = await apiRequest(`/recommendations/history/${rec.id}/save/`, {
      method: "POST",
    });
    if (res.ok) {
      const res2 = await apiRequest("/favorites/", {
        method: "POST",
        body: { recommendation: rec.id },
      });
      if (res2.ok) showToast("Saved to Favorites!", "success");
    }
  });

  qs<HTMLButtonElement>("#try-this-rec-btn").addEventListener("click", () => {
    setSelectedRecommendation(rec);
    generateVirtualTryOn();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();
  renderSidebar("sidebar-mount", "/pages/recommendations.html");

  // Load user photo on page load
  loadUserPhoto();

  // Photo Upload Event Listeners
  const fileInput = qs<HTMLInputElement>("#photo-file-input");
  const fileInputReplace = qs<HTMLInputElement>("#photo-file-input-replace");

  fileInput.addEventListener("change", (e) => {
    const files = (e.target as HTMLInputElement).files;
    if (files && files.length > 0) handlePhotoSelect(files[0]);
  });

  fileInputReplace.addEventListener("change", (e) => {
    const files = (e.target as HTMLInputElement).files;
    if (files && files.length > 0) handlePhotoSelect(files[0]);
  });

  qs<HTMLButtonElement>("#photo-confirm-upload-btn").addEventListener("click", uploadPendingPhoto);
  qs<HTMLButtonElement>("#photo-cancel-upload-btn").addEventListener("click", () => {
    renderPhotoState(!!currentUserPhoto);
  });
  qs<HTMLButtonElement>("#photo-delete-btn").addEventListener("click", deleteUserPhoto);
  qs<HTMLButtonElement>("#tryon-alert-close").addEventListener("click", hideTryOnAlert);

  // Try-On Buttons Event Listeners
  qs<HTMLButtonElement>("#try-outfit-btn").addEventListener("click", generateVirtualTryOn);
  qs<HTMLButtonElement>("#try-another-btn").addEventListener("click", handleTryAnother);

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

    const btn = qs<HTMLButtonElement>("#generate-btn");
    btn.disabled = true;
    btn.textContent =
      (detectedLat !== null && detectedLon !== null) || city
        ? "Checking Weather..."
        : "Generating...";

    const res = await apiRequest<{
      success: boolean;
      recommendation?: Recommendation;
      message?: string;
    }>("/recommendations/generate/", {
      method: "POST",
      body: {
        season,
        occasion,
        city: city === "Detected Location" ? "" : city,
        latitude: detectedLat,
        longitude: detectedLon,
      },
    });

    btn.disabled = false;
    btn.textContent = "Generate Outfit";

    if (res.ok && res.data.recommendation) {
      renderRecommendation(res.data.recommendation);
    } else {
      showToast(
        res.data.message || "Could not generate a recommendation. Add more wardrobe items.",
        "error"
      );
    }
  });
});

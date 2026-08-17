import { requireAuth } from "../auth.js";
import { renderSidebar } from "../components/navbar.js";
import { apiRequest } from "../api.js";
import { qs, getImageUrl } from "../utils.js";
import { showToast } from "../components/toast.js";

interface TravelPlan {
  id: number;
  destination_city: string;
  destination_country: string;
  start_date: string;
  end_date: string;
  trip_purpose: string;
  avg_temperature_c: number;
  min_temperature_c: number;
  max_temperature_c: number;
  weather_condition: string;
  weather_summary: string;
  packing_list: string[];
  outfit_suggestions: { id: number; name: string; category: string; image: string | null }[];
}

function renderPlanResult(plan: TravelPlan): void {
  const container = qs<HTMLElement>("#travel-result");
  container.classList.remove("hidden");
  container.innerHTML = `
    <div class="card mb-6">
      <div class="mb-4 flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-ink-900">${plan.destination_city}${plan.destination_country ? ", " + plan.destination_country : ""}</h3>
          <p class="text-sm text-gray-500">${plan.start_date} &rarr; ${plan.end_date}</p>
        </div>
        <span class="badge">${plan.weather_condition}</span>
      </div>
      <p class="mb-4 text-sm text-gray-600">${plan.weather_summary}</p>
      <div class="grid grid-cols-3 gap-4 text-center">
        <div class="rounded-lg bg-voa-50 p-3">
          <p class="text-xs text-gray-500">Average</p>
          <p class="text-lg font-semibold text-voa-700">${plan.avg_temperature_c}&deg;C</p>
        </div>
        <div class="rounded-lg bg-voa-50 p-3">
          <p class="text-xs text-gray-500">Low</p>
          <p class="text-lg font-semibold text-voa-700">${plan.min_temperature_c}&deg;C</p>
        </div>
        <div class="rounded-lg bg-voa-50 p-3">
          <p class="text-xs text-gray-500">High</p>
          <p class="text-lg font-semibold text-voa-700">${plan.max_temperature_c}&deg;C</p>
        </div>
      </div>
    </div>

    <div class="card">
      <h4 class="mb-4 font-semibold text-ink-900">Outfit Suggestions from Your Wardrobe</h4>
      ${plan.outfit_suggestions.length ? `
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          ${plan.outfit_suggestions.map((item) => `
            <div class="rounded-xl border border-gray-100 p-2.5 text-center transition-all hover:shadow-card hover:border-voa-200">
              <div class="mb-2 h-36 w-full overflow-hidden rounded-lg bg-voa-50">
                ${item.image ? `<img src="${getImageUrl(item.image)}" class="h-full w-full object-cover" />` : `<div class="flex h-full items-center justify-center text-xs text-voa-300">No Image</div>`}
              </div>
              <p class="truncate text-xs font-semibold text-ink-900">${item.name}</p>
              ${item.category ? `<span class="mt-1 inline-block rounded-full bg-voa-50 px-2 py-0.5 text-[10px] font-medium text-voa-700 capitalize">${item.category}</span>` : ""}
            </div>`).join("")}
        </div>` : `<p class="text-sm text-gray-500">Add wardrobe items for this season to get outfit suggestions.</p>`}
    </div>
  `;
}

async function loadPastPlans(): Promise<void> {
  const res = await apiRequest<{ results: TravelPlan[] }>("/travel/plans/");
  const list = qs<HTMLElement>("#past-plans-list");
  if (!res.ok) return;
  const plans = res.data.results || [];
  list.innerHTML = plans.length
    ? plans.map((p) => `
      <button data-plan-id="${p.id}" class="w-full rounded-lg border border-gray-100 p-3 text-left text-sm hover:border-voa-300">
        <p class="font-medium">${p.destination_city}</p>
        <p class="text-xs text-gray-500">${p.start_date} &rarr; ${p.end_date}</p>
      </button>`).join("")
    : `<p class="text-sm text-gray-500">No past trips yet.</p>`;

  list.querySelectorAll<HTMLButtonElement>("[data-plan-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const plan = plans.find((p) => p.id === Number(btn.dataset.planId));
      if (plan) renderPlanResult(plan);
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();
  renderSidebar("sidebar-mount", "/pages/travel-planner.html");
  loadPastPlans();

  qs<HTMLFormElement>("#travel-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      destination_city: qs<HTMLInputElement>("#destination_city").value.trim(),
      destination_country: qs<HTMLSelectElement>("#destination_country").value,
      start_date: qs<HTMLInputElement>("#start_date").value,
      end_date: qs<HTMLInputElement>("#end_date").value,
      trip_purpose: qs<HTMLSelectElement>("#trip_purpose").value,
    };

    const btn = qs<HTMLButtonElement>("#plan-trip-btn");
    btn.disabled = true;
    btn.textContent = "Fetching weather...";

    const res = await apiRequest<TravelPlan>("/travel/plans/", { method: "POST", body: payload });

    btn.disabled = false;
    btn.textContent = "Plan My Trip";

    if (res.ok) {
      renderPlanResult(res.data);
      loadPastPlans();
      showToast("Trip planned successfully!", "success");
    } else {
      showToast((res.data as any).message || "Could not fetch weather for this destination.", "error");
    }
  });
});

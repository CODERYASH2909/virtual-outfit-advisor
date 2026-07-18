import { getCurrentUser, logout } from "../auth.js";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/pages/dashboard.html", icon: "grid" },
  { label: "Wardrobe", href: "/pages/wardrobe.html", icon: "shirt" },
  { label: "Recommendations", href: "/pages/recommendations.html", icon: "sparkles" },
  { label: "Travel Planner", href: "/pages/travel-planner.html", icon: "plane" },
  { label: "Favorites", href: "/pages/favorites.html", icon: "heart" },
  { label: "History", href: "/pages/history.html", icon: "clock" },
  { label: "Profile", href: "/pages/profile.html", icon: "user" },
];

function ensureMobileTopbar(): void {
  if (document.getElementById("voa-mobile-topbar")) return;
  const bar = document.createElement("div");
  bar.id = "voa-mobile-topbar";
  bar.className = "sticky top-0 z-40 flex items-center justify-between border-b border-gray-100 bg-white px-4 py-3 lg:hidden";
  bar.innerHTML = `
    <div class="brand-orbit" aria-label="Virtual Outfit Advisor">
      <span class="brand-orbit-mark" aria-hidden="true">
        <span class="brand-orbit-cube"></span>
        <span class="brand-orbit-ring"></span>
      </span>
      <span class="font-display text-lg font-semibold text-ink-900">Virtual Outfit Advisor</span>
    </div>
    <button id="voa-mobile-menu-btn" class="rounded-lg border border-gray-200 p-2 text-gray-600">☰</button>
  `;
  document.body.prepend(bar);

  document.getElementById("voa-mobile-menu-btn")?.addEventListener("click", () => {
    const sidebar = document.querySelector("aside");
    sidebar?.classList.toggle("hidden");
    sidebar?.classList.toggle("fixed");
    sidebar?.classList.toggle("inset-0");
    sidebar?.classList.toggle("z-50");
  });
}

export function renderSidebar(mountId: string, activeHref: string): void {
  const mount = document.getElementById(mountId);
  if (!mount) return;
  const user = getCurrentUser();
  ensureMobileTopbar();

  mount.innerHTML = `
    <div class="flex h-full flex-col justify-between">
      <div>
        <div class="brand-orbit mb-8 px-2" aria-label="Virtual Outfit Advisor">
          <span class="brand-orbit-mark" aria-hidden="true">
            <span class="brand-orbit-cube"></span>
            <span class="brand-orbit-ring"></span>
          </span>
          <span class="font-display text-lg font-semibold text-ink-900">Virtual Outfit Advisor</span>
        </div>
        <nav class="flex flex-col gap-1">
          ${NAV_ITEMS.map(
            (item) => `
            <a href="${item.href}" class="sidebar-link ${activeHref === item.href ? "sidebar-link-active" : ""}">
              <span>${item.label}</span>
            </a>`
          ).join("")}
        </nav>
      </div>
      <div class="border-t border-gray-100 pt-4">
        <div class="mb-3 flex items-center gap-3 px-2">
          <div class="flex h-9 w-9 items-center justify-center rounded-full bg-voa-100 text-voa-700 font-semibold">
            ${user ? user.first_name.charAt(0).toUpperCase() : "U"}
          </div>
          <div class="text-sm">
            <p class="font-medium text-ink-900">${user ? `${user.first_name} ${user.last_name}` : "Guest"}</p>
            <p class="text-xs text-gray-500">${user ? user.email : ""}</p>
          </div>
        </div>
        <button id="voa-logout-btn" class="sidebar-link w-full text-left text-rose-600 hover:bg-rose-50 hover:text-rose-700">
          Log out
        </button>
      </div>
    </div>
  `;

  document.getElementById("voa-logout-btn")?.addEventListener("click", logout);
}

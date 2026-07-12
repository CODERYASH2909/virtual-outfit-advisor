type ToastType = "success" | "error" | "info";

function ensureContainer(): HTMLElement {
  let container = document.getElementById("voa-toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "voa-toast-container";
    container.className = "fixed top-5 right-5 z-[100] flex flex-col gap-3";
    document.body.appendChild(container);
  }
  return container;
}

export function showToast(message: string, type: ToastType = "info"): void {
  const container = ensureContainer();
  const colors: Record<ToastType, string> = {
    success: "bg-emerald-600",
    error: "bg-rose-600",
    info: "bg-voa-600",
  };

  const toast = document.createElement("div");
  toast.className = `${colors[type]} text-white px-5 py-3 rounded-xl shadow-premium text-sm font-medium max-w-sm animate-[fadeIn_0.2s_ease-out]`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = "opacity 0.3s ease";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

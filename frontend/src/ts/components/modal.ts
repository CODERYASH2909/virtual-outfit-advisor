export function openModal(id: string): void {
  document.getElementById(id)?.classList.remove("hidden");
}

export function closeModal(id: string): void {
  document.getElementById(id)?.classList.add("hidden");
}

export function bindModalDismiss(id: string, dismissSelector = "[data-modal-dismiss]"): void {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.querySelectorAll(dismissSelector).forEach((el) =>
    el.addEventListener("click", () => closeModal(id))
  );
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal(id);
  });
}

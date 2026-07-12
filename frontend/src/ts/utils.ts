export function qs<T extends HTMLElement>(selector: string, parent: ParentNode = document): T {
  const el = parent.querySelector(selector);
  if (!el) throw new Error(`Element not found for selector: ${selector}`);
  return el as T;
}

export function qsa<T extends HTMLElement>(selector: string, parent: ParentNode = document): T[] {
  return Array.from(parent.querySelectorAll(selector)) as T[];
}

export function debounce<F extends (...args: any[]) => void>(fn: F, delay = 300): F {
  let timer: ReturnType<typeof setTimeout>;
  return ((...args: any[]) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  }) as F;
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function titleCase(str: string): string {
  return str.replace(/_/g, " ").replace(/\w\S*/g, (t) => t.charAt(0).toUpperCase() + t.slice(1).toLowerCase());
}

export function buildQueryString(params: Record<string, string | number | boolean | undefined>): string {
  const usable = Object.entries(params).filter(([, v]) => v !== undefined && v !== "");
  if (usable.length === 0) return "";
  const search = new URLSearchParams(usable.map(([k, v]) => [k, String(v)]));
  return `?${search.toString()}`;
}

export function formatMoney(value: number, currency = "VND"): string {
  return `${value.toLocaleString("vi-VN")} ${currency}`;
}

export function formatSlotValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "boolean") return value ? "có" : "không";
  return String(value);
}

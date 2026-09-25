const COMPANY_KEY = "kva_company_id";
const SESSION_KEY = "kva_session_id";

export function getCompanyId(): string {
  if (typeof window === "undefined") return "demo";
  let value = localStorage.getItem(COMPANY_KEY);
  if (!value) {
    value = "demo";
    localStorage.setItem(COMPANY_KEY, value);
  }
  return value;
}

export function setCompanyId(companyId: string): void {
  localStorage.setItem(COMPANY_KEY, companyId);
}

export function getSessionId(): string {
  if (typeof window === "undefined") return "";
  let value = localStorage.getItem(SESSION_KEY);
  if (!value) {
    value = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, value);
  }
  return value;
}

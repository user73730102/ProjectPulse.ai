/**
 * lib/api.ts
 * Typed API client for all backend endpoints.
 * Uses fetch with JWT token from localStorage.
 */

// Use the environment variable, which must be injected at build time.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Auth helpers ──────────────────────────────────────────────────────────

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("pulse_token");
}

export function setToken(token: string) {
  localStorage.setItem("pulse_token", token);
}

export function clearToken() {
  localStorage.removeItem("pulse_token");
  localStorage.removeItem("pulse_user");
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });

  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API request failed");
  }

  return res.json();
}

// ─── Types ─────────────────────────────────────────────────────────────────

export type UserRole = "contractor" | "engineer" | "auditor" | "pm";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface Document {
  id: number;
  filename: string;
  original_name: string;
  doc_type: string;
  project_id: string | null;
  page_count: number | null;
  is_processed: boolean;
  uploaded_at: string;
}

export interface SpecSection {
  id: number;
  clause_number: string | null;
  clause_title: string | null;
  content: string;
  page_number: number | null;
  chunk_index: number;
}

export interface Submittal {
  id: number;
  submittal_number: string;
  title: string;
  vendor_name: string | null;
  spec_section_ref: string | null;
  submitted_value: string | null;
  status: string;
  submitted_at: string;
  reviewed_at: string | null;
}

export interface SubmittalDetail extends Submittal {
  ncrs: NCRSummary[];
}

export interface NCRSummary {
  id: number;
  ncr_number: string;
  severity: string | null;
  status: string;
  deviation_description: string;
  ai_confidence: number | null;
}

export interface NCR {
  id: number;
  ncr_number: string;
  submittal_id: number | null;
  clause_id: number | null;
  test_record_id?: number | null;
  required_value: string | null;
  submitted_value: string | null;
  deviation_description: string;
  severity: string | null;
  status: string;
  ai_confidence: number | null;
  created_at: string;
  updated_at: string | null;
  // Detail fields
  clause_number?: string;
  clause_title?: string;
  clause_content?: string;
  clause_page?: number;
  submittal_number?: string;
  vendor_name?: string;
}

export interface Citation {
  document_id: number | null;
  document_name: string | null;
  file_path?: string | null;
  clause_number: string | null;
  page: number | null;
  excerpt: string | null;
}

export interface RFIResponse {
  entry_id: number | null;
  question: string;
  answer: string | null;
  citations: Citation[];
  error: string | null;
}

export interface RFIHistoryItem {
  id: number;
  question: string;
  answer: string | null;
  citations: Citation[] | null;
  created_at: string;
}

// ─── Auth API ──────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<User> {
  const params = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API_BASE}/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: params.toString(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Login failed");
  }
  const data = await res.json();
  setToken(data.access_token);

  const user = await getMe();
  localStorage.setItem("pulse_user", JSON.stringify(user));
  return user;
}

export async function getMe(): Promise<User> {
  return request<User>("/me");
}

// ─── Documents API ─────────────────────────────────────────────────────────

export async function listDocuments(params?: { doc_type?: string; project_id?: string }): Promise<Document[]> {
  const q = new URLSearchParams(params as Record<string, string>).toString();
  return request<Document[]>(`/documents/${q ? `?${q}` : ""}`);
}

export async function uploadDocument(file: File, docType: string, project_id?: string): Promise<Document> {
  const form = new FormData();
  form.append("file", file);
  form.append("doc_type", docType);
  if (project_id) form.append("project_id", project_id);

  const headers = authHeaders() as Record<string, string>;
  delete headers["Content-Type"];

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    headers,
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function getDocumentChunks(docId: number): Promise<SpecSection[]> {
  return request<SpecSection[]>(`/documents/${docId}/chunks`);
}

export async function deleteDocument(docId: number): Promise<{ detail: string }> {
  return request<{ detail: string }>(`/documents/${docId}`, { method: "DELETE" });
}

// ─── Submittals API ────────────────────────────────────────────────────────

export async function listSubmittals(params?: { status?: string; spec_section_ref?: string }): Promise<Submittal[]> {
  const q = new URLSearchParams(params as Record<string, string>).toString();
  return request<Submittal[]>(`/submittals/${q ? `?${q}` : ""}`);
}

export async function getSubmittal(id: number): Promise<SubmittalDetail> {
  return request<SubmittalDetail>(`/submittals/${id}`);
}

export async function uploadSubmittal(file: File): Promise<SubmittalDetail[]> {
  const form = new FormData();
  form.append("file", file);
  
  const headers = authHeaders() as Record<string, string>;
  delete headers["Content-Type"]; // Let browser set multipart boundary
  
  const res = await fetch(`${API_BASE}/submittals/upload`, {
    method: "POST",
    headers,
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

// ─── NCR API ───────────────────────────────────────────────────────────────

export async function listNCRs(params?: { status?: string; severity?: string; submittal_id?: number }): Promise<NCR[]> {
  const q = new URLSearchParams(
    Object.fromEntries(Object.entries(params || {}).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)]))
  ).toString();
  return request<NCR[]>(`/ncr/${q ? `?${q}` : ""}`);
}

export async function getNCR(id: number): Promise<NCR> {
  return request<NCR>(`/ncr/${id}`);
}

export async function approveNCR(id: number): Promise<NCR> {
  return request<NCR>(`/ncr/${id}/approve`, { method: "PATCH", body: JSON.stringify({}) });
}

export async function voidNCR(id: number): Promise<NCR> {
  return request<NCR>(`/ncr/${id}/void`, { method: "PATCH" });
}

// ─── Agents API ────────────────────────────────────────────────────────────

export async function runComplianceCheck(submittalId: number): Promise<{ ncrs_created: number; ncr_ids: number[]; error?: string }> {
  return request(`/agents/compliance/run/${submittalId}`, { method: "POST" });
}

export async function queryRFI(question: string): Promise<RFIResponse> {
  return request<RFIResponse>("/agents/rfi/query", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

export async function getRFIHistory(limit = 20): Promise<RFIHistoryItem[]> {
  return request<RFIHistoryItem[]>(`/agents/rfi/history?limit=${limit}`);
}

// --- Phase 2 Agents API --------------------------------------------------

export interface CommissioningTest {
  id: string;
  system: string;
  status: string;
  progress: number;
  failedPoints: number;
  totalPoints: number;
  lastUpdated: string;
  record_id: number | null;
}

export async function listCommissioningTests(): Promise<CommissioningTest[]> {
  return request<CommissioningTest[]>("/commissioning/tests");
}

export async function evaluateTest(recordId: number): Promise<any> {
  return request(`/commissioning/evaluate/${recordId}`, { method: "POST" });
}

export interface ScheduleRisk {
  id: string;
  task: string;
  driver: string;
  description: string;
  impact: string;
  severity: string;
  mitigations: string[];
}

export async function listScheduleRisks(): Promise<ScheduleRisk[]> {
  return request<ScheduleRisk[]>("/schedule/risks");
}

export async function runScheduleAnalysis(): Promise<any> {
  return request("/schedule/analyze", { method: "POST" });
}

export interface Shipment {
  id: string;
  equipment: string;
  vendor: string;
  origin: string;
  destination: string;
  status: string;
  location: string;
  eta: string;
  riskFlag: string | null;
  delayEstimate: string | null;
  shipment_db_id: number;
}

export async function listShipments(): Promise<Shipment[]> {
  return request<Shipment[]>("/supply-chain/shipments");
}

export async function evaluateShipment(shipmentId: number): Promise<any> {
  return request(`/supply-chain/evaluate/${shipmentId}`, { method: "POST" });
}


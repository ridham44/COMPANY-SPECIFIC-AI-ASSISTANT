const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type DocumentStatus = "processing" | "indexed" | "failed";

export interface KnowledgeDocument {
  id: string;
  filename: string;
  category: string | null;
  status: DocumentStatus;
  chunk_count: number;
  error_message: string | null;
  version: number;
}

export interface SourceRef {
  document_name: string;
  page: number | null;
}

export interface ChatResult {
  answer: string;
  sources: SourceRef[];
  grounded: boolean;
}

export interface ConversationSummary {
  id: string;
  session_id: string;
}

export interface Message {
  role: string;
  content: string;
  sources: SourceRef[];
  grounded: boolean | null;
}

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with ${response.status}`);
  }
  return response.json();
}

export async function listDocuments(companyId: string): Promise<KnowledgeDocument[]> {
  const res = await fetch(`${API_BASE_URL}/documents?company_id=${encodeURIComponent(companyId)}`);
  return handle(res);
}

export async function uploadDocument(companyId: string, file: File, category?: string): Promise<KnowledgeDocument> {
  const form = new FormData();
  form.append("company_id", companyId);
  if (category) form.append("category", category);
  form.append("file", file);
  const res = await fetch(`${API_BASE_URL}/documents/upload`, { method: "POST", body: form });
  return handle(res);
}

export async function deleteDocument(companyId: string, documentId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}?company_id=${encodeURIComponent(companyId)}`, {
    method: "DELETE",
  });
  await handle(res);
}

export async function reindexDocument(companyId: string, documentId: string): Promise<KnowledgeDocument> {
  const res = await fetch(
    `${API_BASE_URL}/documents/${documentId}/reindex?company_id=${encodeURIComponent(companyId)}`,
    { method: "POST" },
  );
  return handle(res);
}

export async function sendChatMessage(companyId: string, sessionId: string, message: string): Promise<ChatResult> {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, company_id: companyId, session_id: sessionId }),
  });
  return handle(res);
}

export async function listConversations(companyId: string, sessionId: string): Promise<ConversationSummary[]> {
  const res = await fetch(
    `${API_BASE_URL}/conversations?company_id=${encodeURIComponent(companyId)}&session_id=${encodeURIComponent(sessionId)}`,
  );
  return handle(res);
}

export async function getMessages(companyId: string, conversationId: string): Promise<Message[]> {
  const res = await fetch(
    `${API_BASE_URL}/conversations/${conversationId}/messages?company_id=${encodeURIComponent(companyId)}`,
  );
  return handle(res);
}

export async function deleteConversation(companyId: string, conversationId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/conversations/${conversationId}?company_id=${encodeURIComponent(companyId)}`, {
    method: "DELETE",
  });
  await handle(res);
}

"use client";

import { useEffect, useRef, useState } from "react";
import {
  ConversationSummary,
  Message,
  deleteConversation,
  getMessages,
  listConversations,
  sendChatMessage,
} from "@/lib/api";
import { getCompanyId, getSessionId } from "@/lib/session";

export default function ChatPage() {
  const [companyId, setCompanyIdState] = useState("demo");
  const [sessionId, setSessionIdState] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = getCompanyId();
    const session = getSessionId();
    setCompanyIdState(id);
    setSessionIdState(session);
    refreshConversations(id, session);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function refreshConversations(id: string, session: string) {
    const list = await listConversations(id, session);
    setConversations(list);
    if (list.length > 0) {
      setMessages(await getMessages(id, list[0].id));
    }
  }

  async function handleSend() {
    if (!input.trim() || sending) return;
    const question = input.trim();
    setInput("");
    setSending(true);
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: question, sources: [], grounded: null }]);
    try {
      const result = await sendChatMessage(companyId, sessionId, question);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.answer, sources: result.sources, grounded: result.grounded },
      ]);
      refreshConversations(companyId, sessionId);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSending(false);
    }
  }

  async function handleDeleteConversation(conversationId: string) {
    await deleteConversation(companyId, conversationId);
    setMessages([]);
    refreshConversations(companyId, sessionId);
  }

  return (
    <div className="chat-layout">
      <aside className="conversation-list">
        <h2>Conversations</h2>
        {conversations.map((c) => (
          <div key={c.id} className="conversation-item">
            <button onClick={async () => setMessages(await getMessages(companyId, c.id))}>{c.session_id}</button>
            <button className="delete" onClick={() => handleDeleteConversation(c.id)}>
              x
            </button>
          </div>
        ))}
        {conversations.length === 0 && <p className="hint">No conversations yet.</p>}
      </aside>

      <section className="chat-panel">
        <div className="messages">
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.role}`}>
              <div className="bubble">{m.content}</div>
              {m.sources.length > 0 && (
                <div className="sources">
                  {m.sources.map((s, si) => (
                    <span key={si} className="source-chip">
                      {s.document_name}
                      {s.page ? ` (p.${s.page})` : ""}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {error && <p className="error">{error}</p>}

        <div className="composer">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask a question about your documents..."
            disabled={sending}
          />
          <button onClick={handleSend} disabled={sending}>
            {sending ? "Thinking..." : "Send"}
          </button>
        </div>
      </section>
    </div>
  );
}

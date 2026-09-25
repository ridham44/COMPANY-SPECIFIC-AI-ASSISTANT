"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { KnowledgeDocument, deleteDocument, listDocuments, reindexDocument, uploadDocument } from "@/lib/api";
import { getCompanyId } from "@/lib/session";

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [companyId, setCompanyIdState] = useState("demo");
  const [isDragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async (id: string) => {
    try {
      setDocuments(await listDocuments(id));
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    const id = getCompanyId();
    setCompanyIdState(id);
    refresh(id);
    const interval = setInterval(() => refresh(id), 4000);
    return () => clearInterval(interval);
  }, [refresh]);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setError(null);
    for (const file of Array.from(files)) {
      try {
        await uploadDocument(companyId, file);
      } catch (e) {
        setError((e as Error).message);
      }
    }
    refresh(companyId);
  }

  async function handleDelete(documentId: string) {
    if (!confirm("Delete this document?")) return;
    await deleteDocument(companyId, documentId);
    refresh(companyId);
  }

  async function handleReindex(documentId: string) {
    await reindexDocument(companyId, documentId);
    refresh(companyId);
  }

  return (
    <div>
      <h1>Knowledge Base</h1>
      <p className="hint">Upload PDF, DOCX or TXT files. They're parsed, chunked and indexed automatically.</p>

      <div
        className={`dropzone ${isDragging ? "dragging" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        Drag & drop files here, or click to browse
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt"
          hidden
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {error && <p className="error">{error}</p>}

      <table className="doc-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Chunks</th>
            <th>Version</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id}>
              <td>{doc.filename}</td>
              <td>
                <span className={`badge ${doc.status}`}>{doc.status}</span>
                {doc.status === "failed" && doc.error_message && (
                  <span className="error-text"> - {doc.error_message}</span>
                )}
              </td>
              <td>{doc.chunk_count}</td>
              <td>{doc.version}</td>
              <td>
                <button onClick={() => handleReindex(doc.id)}>Re-index</button>
                <button onClick={() => handleDelete(doc.id)}>Delete</button>
              </td>
            </tr>
          ))}
          {documents.length === 0 && (
            <tr>
              <td colSpan={5} className="empty">
                No documents yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getCompanyId, setCompanyId } from "@/lib/session";

export default function WorkspaceBar() {
  const [companyId, setCompanyIdState] = useState("demo");
  const pathname = usePathname();

  useEffect(() => {
    setCompanyIdState(getCompanyId());
  }, []);

  function handleBlur() {
    setCompanyId(companyId);
    window.location.reload();
  }

  return (
    <header className="topbar">
      <div className="brand">Company Knowledge Assistant</div>
      <nav>
        <Link href="/knowledge-base" className={pathname === "/knowledge-base" ? "active" : ""}>
          Knowledge Base
        </Link>
        <Link href="/chat" className={pathname === "/chat" ? "active" : ""}>
          Chat
        </Link>
      </nav>
      <div className="workspace">
        <label htmlFor="company-id">Workspace</label>
        <input
          id="company-id"
          value={companyId}
          onChange={(e) => setCompanyIdState(e.target.value)}
          onBlur={handleBlur}
          onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
        />
      </div>
    </header>
  );
}

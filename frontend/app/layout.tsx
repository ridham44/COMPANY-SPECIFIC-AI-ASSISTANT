import "./globals.css";
import WorkspaceBar from "@/components/WorkspaceBar";

export const metadata = {
  title: "Company Knowledge Assistant",
  description: "Ask questions over your own uploaded documents.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <WorkspaceBar />
        <main className="page">{children}</main>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chorus Agent Dashboard",
  description: "Admin dashboard for your personal AI agent",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}

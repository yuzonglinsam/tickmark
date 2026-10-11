import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: { default: "Tickmark — the AI credit analyst that shows its work", template: "%s · Tickmark" },
  description:
    "An AI-assisted corporate credit research terminal. Every figure is computed from SEC XBRL filings and ticks back to its source; AI explains, never invents.",
  openGraph: {
    title: "Tickmark — the AI credit analyst that shows its work",
    description:
      "Credit metrics, rating-threshold headroom, debt maturity walls and cited AI memos for 490+ issuers — every number traced to its SEC filing.",
    type: "website",
  },
};

export const viewport: Viewport = { themeColor: "#06080b", colorScheme: "dark" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark h-full antialiased">
      <body className="min-h-full flex flex-col">
        <TooltipProvider delayDuration={150}>{children}</TooltipProvider>
        <Toaster theme="dark" position="bottom-right" />
      </body>
    </html>
  );
}

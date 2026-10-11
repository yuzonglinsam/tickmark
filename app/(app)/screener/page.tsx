import type { Metadata } from "next";
import { Screener } from "@/components/terminal/screener";
import { getUniverse } from "@/lib/server-data";

export const metadata: Metadata = { title: "Screener" };

export default function ScreenerPage() {
  return <Screener u={getUniverse()} />;
}

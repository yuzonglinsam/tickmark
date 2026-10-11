import type { Metadata } from "next";
import { TerminalHome } from "@/components/terminal/terminal-home";
import { getUniverse } from "@/lib/server-data";

export const metadata: Metadata = { title: "Terminal" };

export default function TerminalPage() {
  return <TerminalHome u={getUniverse()} />;
}

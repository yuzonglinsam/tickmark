"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search } from "lucide-react";
import { GithubIcon } from "@/components/brand/github";
import { Logo } from "@/components/brand/logo";
import { CommandMenu, openCommandMenu } from "./command-menu";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/terminal", label: "Terminal" },
  { href: "/screener", label: "Screener" },
  { href: "/methodology", label: "Methodology" },
];

export const REPO_URL = process.env.NEXT_PUBLIC_REPO_URL || "https://github.com/";

export function TopNav({ asOf }: { asOf?: string }) {
  const path = usePathname();
  return (
    <header className="sticky top-0 z-40 border-b border-hairline bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-[1480px] items-center gap-3 px-4 sm:gap-6 sm:px-6">
        <Link href="/" className="shrink-0" aria-label="Tickmark home">
          <Logo />
        </Link>
        <nav className="hidden items-center gap-1 md:flex">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={cn(
                "rounded-md px-3 py-1.5 text-[13px] text-ink-2 transition-colors hover:bg-accent hover:text-ink-1",
                path.startsWith(n.href) && "bg-accent text-ink-1",
              )}
            >
              {n.label}
            </Link>
          ))}
        </nav>
        <button
          onClick={openCommandMenu}
          className="group ml-auto flex h-9 min-w-0 flex-1 max-w-[360px] items-center gap-2 rounded-lg border border-hairline-strong bg-panel px-3 text-left text-[13px] text-ink-3 transition-colors hover:border-amber/40 hover:text-ink-2"
        >
          <Search className="size-4" />
          <span className="flex-1 truncate">Search any SEC filer…</span>
          <kbd className="num hidden rounded border border-hairline-strong px-1.5 py-0.5 text-[10px] sm:inline">⌘K</kbd>
        </button>
        {asOf && (
          <span className="hidden items-center gap-2 text-[11px] text-ink-3 xl:flex">
            <span className="size-1.5 rounded-full bg-good shadow-[0_0_8px_var(--good)]" />
            SEC data · {asOf}
          </span>
        )}
        <a href={REPO_URL} target="_blank" rel="noreferrer" className="hidden text-ink-3 hover:text-ink-1 sm:block" aria-label="Source code on GitHub">
          <GithubIcon className="size-[18px]" />
        </a>
      </div>
      <nav className="flex items-center gap-1 overflow-x-auto border-t border-hairline px-3 py-1.5 md:hidden">
        {NAV.map((n) => (
          <Link key={n.href} href={n.href} className={cn("rounded-md px-3 py-1 text-[12.5px] text-ink-2", path.startsWith(n.href) && "bg-accent text-ink-1")}>
            {n.label}
          </Link>
        ))}
      </nav>
      <CommandMenu />
    </header>
  );
}

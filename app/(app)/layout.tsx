import { TopNav } from "@/components/shell/top-nav";
import { getUniverse } from "@/lib/server-data";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const u = getUniverse();
  return (
    <div className="flex min-h-screen flex-col">
      <TopNav asOf={u.generated_at.slice(0, 10)} />
      <main className="flex-1">{children}</main>
      <footer className="border-t border-hairline py-6 text-center text-[11.5px] text-ink-3">
        Tickmark · Built by Sam Yu · Data: SEC EDGAR XBRL (public domain) · Not investment advice; indicative profiles are not credit ratings.
      </footer>
    </div>
  );
}

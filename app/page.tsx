import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { Landing, type LandingStats } from "@/components/landing/landing";
import { getUniverse } from "@/lib/server-data";

function countFacts(): number {
  // Number of distinct SEC facts referenced across the dataset (computed at build time).
  const dir = path.join(process.cwd(), "public", "data", "issuers");
  let n = 0;
  for (const f of readdirSync(dir)) {
    const doc = JSON.parse(readFileSync(path.join(dir, f), "utf8"));
    n += Object.keys(doc.sources ?? {}).length;
  }
  return n;
}

export default function Home() {
  const u = getUniverse();
  const s: LandingStats = {
    issuers: u.count,
    memos: u.issuers.filter((r) => r.memo).length,
    facts: countFacts(),
    hk: u.issuers.filter((r) => r.hk).length,
    sectors: Object.keys(u.sectors).length,
    asOf: u.generated_at.slice(0, 10),
    tape: u.issuers.slice(0, 40).map((r) => ({ t: r.t, tier: r.tier })),
  };
  return <Landing s={s} />;
}

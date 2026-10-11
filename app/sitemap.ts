import type { MetadataRoute } from "next";
import { getUniverse } from "@/lib/server-data";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
  const u = getUniverse();
  return [
    { url: `${base}/`, priority: 1 },
    { url: `${base}/terminal`, priority: 0.9 },
    { url: `${base}/screener`, priority: 0.8 },
    { url: `${base}/methodology`, priority: 0.6 },
    ...u.issuers.map((r) => ({ url: `${base}/i/${r.t}`, priority: 0.5 })),
  ];
}

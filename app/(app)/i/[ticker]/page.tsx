import type { Metadata } from "next";
import { IssuerView } from "@/components/issuer/issuer-view";
import { getUniverse } from "@/lib/server-data";

type Props = { params: Promise<{ ticker: string }> };

// Covered issuers are prerendered; any other ticker renders on demand and is analysed live.
export function generateStaticParams() {
  return getUniverse().issuers.map((r) => ({ ticker: r.t }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { ticker } = await params;
  const t = decodeURIComponent(ticker).toUpperCase();
  const row = getUniverse().issuers.find((r) => r.t === t);
  return {
    title: row ? `${row.t} · ${row.n}` : t,
    description: row
      ? `${row.n}: credit metrics, indicative financial-risk profile, debt maturities and a cited AI memo — every figure traced to SEC filings.`
      : `Live SEC-based credit analysis for ${t}.`,
  };
}

export default async function IssuerPage({ params }: Props) {
  const { ticker } = await params;
  const t = decodeURIComponent(ticker).toUpperCase();
  const covered = getUniverse().issuers.some((r) => r.t === t);
  return <IssuerView ticker={t} covered={covered} />;
}

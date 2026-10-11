# Third-party software and data

Tickmark's original code is MIT-licensed (see `LICENSE`). It is built on the open-source
projects below, which keep their own licences. Nothing here is vendored except where noted.

## Copied source (adapted)

| Component | Source | Licence | Where |
|---|---|---|---|
| UI primitives (button, dialog, sheet, tabs, tooltip, slider, command, …) | [shadcn/ui](https://github.com/shadcn-ui/ui) `apps/v4/registry/new-york-v4/ui` | MIT | `components/ui/*` — import paths adapted |
| GitHub mark | [Primer Octicons](https://github.com/primer/octicons) | MIT | `components/brand/github.tsx` |
| Next.js + Flask routing pattern | [vercel/examples · nextjs-flask](https://github.com/vercel/examples) | MIT | `next.config.ts` rewrites, `api/index.py` layout |

## Libraries

**Web:** Next.js, React (MIT) · Radix UI (MIT) · cmdk (MIT) · Apache ECharts (Apache-2.0) · echarts-for-react (MIT) ·
Framer Motion (MIT) · Tailwind CSS, tailwind-merge, clsx, tw-animate-css (MIT) · class-variance-authority (Apache-2.0) ·
lucide-react (ISC) · sonner (MIT) · Inter and JetBrains Mono via Fontsource (SIL OFL 1.1).

**Python:** requests (Apache-2.0) · Beautiful Soup (MIT) · Flask (BSD-3) · ReportLab (BSD) · python-dotenv (BSD-3) ·
optional: EdgarTools (MIT) for filing-level reconciliation, pandas (BSD-3), psycopg (LGPL-3.0).

## Methods referenced

- Financial-risk ratio ranges: S&P Global Ratings, *Corporate Methodology* (standard volatility table), a public document.
  Tickmark uses the published ranges only; it does not reproduce S&P ratings or claim equivalence.
- Altman Z″ (1995, non-manufacturing / emerging-market version), academic literature.

## Data

- SEC EDGAR APIs (`data.sec.gov`, `www.sec.gov`) — US government works, public domain. Accessed with a declared
  User-Agent and below SEC's fair-access rate limit.
- DeepSeek API — generates draft memo text and Q&A answers; outputs are labelled as AI-generated drafts.

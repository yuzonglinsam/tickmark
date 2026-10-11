import type { NextConfig } from "next";

// Python serverless functions (api/index.py) serve /api/py/* on Vercel.
// In local development they run as a Flask app on port 5328.
const isDev = process.env.NODE_ENV === "development";

const nextConfig: NextConfig = {
  devIndicators: false,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  // Server routes read the dataset index from disk; make sure it ships with them.
  outputFileTracingIncludes: {
    "/**": ["./public/data/universe.json"],
  },
  async rewrites() {
    // Same pattern as Vercel's Next.js + Flask template: the Flask app in api/index.py
    // receives the original /api/py/* path.
    // API_ORIGIN lets the Flask API run elsewhere (e.g. Render) if preferred.
    const external = process.env.API_ORIGIN;
    const destination = external
      ? `${external.replace(/\/$/, "")}/api/py/:path*`
      : isDev ? "http://127.0.0.1:5328/api/py/:path*" : "/api/";
    return [{ source: "/api/py/:path*", destination }];
  },
  async headers() {
    return [
      {
        source: "/data/:path*",
        headers: [{ key: "Cache-Control", value: "public, max-age=3600, stale-while-revalidate=86400" }],
      },
    ];
  },
};

export default nextConfig;

import type { NextConfig } from "next";

// All browser API calls go to /api/* on this domain and are proxied to the FastAPI
// backend (ADR 0004). Locally that is uvicorn; on Vercel, API_ORIGIN points at the EC2 API.
const apiOrigin = process.env.API_ORIGIN ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiOrigin}/api/:path*` }];
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;

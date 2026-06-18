import type { NextConfig } from "next";
import { fileURLToPath } from "url";
import { dirname } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  devIndicators: false,
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;

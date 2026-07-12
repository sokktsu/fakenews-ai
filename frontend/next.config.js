/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {},
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  // Contact page disabled on the live site (Vercel only) while under
  // construction — remove this block to re-enable. Localhost is unaffected.
  async redirects() {
    if (!process.env.VERCEL) return []
    return [
      { source: '/contact', destination: '/', permanent: false },
    ]
  },
}

module.exports = nextConfig

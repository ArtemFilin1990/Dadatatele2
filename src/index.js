/**
 * B24 Catalog Worker
 * Cloudflare Workers entry point
 */

export default {
  async fetch(request, env) {
    // Serve static assets from the public/ directory
    if (!env.ASSETS) {
      return new Response('Assets not configured', { status: 500 });
    }
    return env.ASSETS.fetch(request);
  },
};

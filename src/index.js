/**
 * B24 Catalog Worker
 * Cloudflare Workers entry point
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Route handling
    if (url.pathname === '/') {
      return new Response('B24 Catalog API', {
        headers: { 'Content-Type': 'text/plain' },
      });
    }

    // Default 404 response
    return new Response('Not Found', { status: 404 });
  },
};

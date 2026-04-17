export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path === '/install') {
      return env.ASSETS.fetch(new Request(new URL('/install.html', request.url), request));
    }

    return env.ASSETS.fetch(request);
  },
};

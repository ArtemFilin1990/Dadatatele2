export default {
  async fetch(request) {
    return new Response('b24-catalog worker placeholder', {
      headers: { 'content-type': 'text/plain' },
    });
  },
};
